import cloudscraper
import uuid

from base64 import b64decode


class LuminatyProxyMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.logger = crawler.spider.logger
        self.username = 'lum-customer-hl_afe4c719-zone-zone1'
        self.password = '8jywfhrmovdh'
        self.super_proxy_url = "http://%s:%s@zproxy.lum-superproxy.io:22225"

    def process_request(self, request, spider):

        # Check session
        session = (request.meta.get("cookiejar")
                   or uuid.uuid1().hex)
        country = request.meta.get("country")
        ip = request.meta.get("ip")

        # Init username
        username = self.username

        # Add session string to session if available
        if session and not ip:
            username = "%s-session-%s" % (
                username,
                session
            )

        # Add country to session if available
        if country and not ip:
            username = "%s-country-%s" % (
                username,
                country
            )

        # If has ip meta, make it priority over session
        if ip:
            username = "%s-ip-%s" % (
                username,
                ip
            )

        # Add proxy to request
        request.meta["proxy"] = self.super_proxy_url % (
            username,
            self.password
        )

        # Remove old authorization if exist
        if request.headers.get("Proxy-Authorization"):
            del request.headers["Proxy-Authorization"]

        self.logger.info(
            'Process request %s with proxy %s' % (
                request.url, request.meta["proxy"]
            )
        )


class BypassCloudfareMiddleware(object):

    allow_retry = 5
    captcha_provider = "2captcha"
    captcha_token = "76228b91f256210cf20e6d8428818e23"

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    @staticmethod
    def is_cloudflare_challenge(response):
        """Test if the given response contains the cloudflare's anti-bot protection"""

        first_cloudfare_text = "jschl_vc"
        second_cloudfare_text = "jschl_answer"
        recaptcha_text = "Why do I have to complete a CAPTCHA"

        cloudfare_test = ((response.status in (503, 429, 403)
                           and response.headers.get("Server", "").startswith(b"cloudflare")
                           and first_cloudfare_text in response.text
                           and second_cloudfare_text in response.text)
                          or (response.status in (503, 429, 403)
                              and recaptcha_text in response.text
                              and response.headers.get("Cookie", "").startswith(b"__cfduid")))

        return cloudfare_test

    def __init__(self, crawler):
        self.logger = crawler.spider.logger

    def load_cookies(self, request, byte=True):
        cookies = {}

        # Load cookies bytes
        cookies_string = request.headers.get("Cookie")
        if byte:
            cookies_string = request.headers.get("Cookie").decode("utf-8")

        # Convert cookie byte
        if cookies_string is not None:
            cookies_elements = [
                element.strip().split("=") for element in cookies_string.split(";")
            ]
            cookies = {
                element[0]: "=".join(element[1:]) for element in cookies_elements
            }

        return cookies

    def get_cftoken(self, url, delay=5, proxy=None):
        session = cloudscraper.create_scraper(
            delay=delay,
            recaptcha={
                "provider": self.captcha_provider,
                "api_key": self.captcha_token
            }
        )
        ip = None

        request_args = {
            "url": url
        }

        if proxy:
            request_args["proxies"] = {
                "http": proxy,
                "https": proxy
            }
            ip = session.get(
                url="https://api.ipify.org/?format=json",
                proxies=request_args.get("proxies")
            ).json().get("ip")

        response = session.get(**request_args)
        response = session.get(**request_args)

        headers = response.request.headers
        cookies = self.load_cookies(response.request, False)

        return cookies, headers, ip

    def process_response(self, request, response, spider):

        if not self.is_cloudflare_challenge(response):
            return response

        # Init request args
        request_args = {}

        # Add proxy if available
        proxy = request.meta.get("proxy")
        if proxy:
            request_args["proxy"] = proxy

        # Add proxy authen if available
        basic_auth = request.headers.get("Proxy-Authorization")
        if basic_auth:
            basic_auth_encoded = basic_auth.decode("utf-8").split()[1]
            username, password = b64decode(basic_auth_encoded).decode("utf-8").split(":")
            root_proxy = proxy.replace(
                "https://", ""
            ).replace(
                "http://", ""
            )
            request_args["proxy"] = "%s:%s@%s" % (
                username,
                password,
                root_proxy
            )

        cookies, headers, ip = self.get_cftoken(
            request.url,
            **request_args
        )

        # Replace cookies
        request.cookies.update(cookies.copy())

        # Replace user agent
        request.headers.update(headers.copy())

        # Dont filter this retry request
        request.dont_filter = True

        # Add ip meta if exist
        if ip:
            request.meta["ip"] = ip

        self.logger.info(
            "Header after cloudfare check: %s" % request.headers
        )

        self.logger.info(
            "Cookies after cloudfare check: %s" % request.cookies
        )

        return request


class BypassRecaptchaMiddleware(object):
    allow_retry = 5

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    @staticmethod
    def is_recaptcha_challenge(response):
        """Test if the given response contains the recaptcha protection"""

        return (
                response.status in (503, 429, 403)
                and response.headers.get("Server", "").startswith(b"cloudflare")
                and 'jschl_vc' in response.text
                and 'jschl_answer' in response.text
        )

    def __init__(self, crawler):
        self.logger = crawler.spider.logger
        self.api_token = "76228b91f256210cf20e6d8428818e23"

    def process_response(self, request, response, spider):

        if not self.is_cloudflare_challenge(response):
            return response

        cookies, user_agent = self.get_cftoken(
            request.url,
            proxy=request.meta.get("proxy")
        )

        request.cookies = cookies
        request.headers["User-Agent"] = user_agent
        request.dont_filter = True

        self.logger.info(
            "Header after cloudfare check: %s" % request.headers
        )

        self.logger.info(
            "Cookies after cloudfare check: %s" % request.cookies
        )

        return request
