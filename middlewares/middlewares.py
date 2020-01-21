import cloudscraper
import uuid


class LuminatyProxyMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.logger = crawler.spider.logger
        self.username = 'lum-customer-hl_afe4c719-zone-zone1'
        self.password = '8jywfhrmovdh'
        self.super_proxy_url = "http://%s-session-%s:%s@zproxy.lum-superproxy.io:22225"

    def process_request(self, request, spider):

        # Check session
        session = request.meta.get("cookiejar")
        country = request.meta.get("country")
        if not session:
            session = uuid.uuid1().hex

        if country:
            username = "%s-country-%s" % (
                self.username,
                country
            )
        else:
            username = self.username

        request.meta["proxy"] = self.super_proxy_url % (
            username,
            session,
            self.password
        )

        self.logger.info(
            'Process request %s with proxy %s' % (
                request.url, request.meta["proxy"]
            )
        )


class BypassCloudfareMiddleware(object):

    allow_retry = 5

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    @staticmethod
    def is_cloudflare_challenge(response):
        """Test if the given response contains the cloudflare's anti-bot protection"""

        return (
                response.status in (503, 429, 403)
                and response.headers.get("Server", "").startswith(b"cloudflare")
                and 'jschl_vc' in response.text
                and 'jschl_answer' in response.text
        )

    def __init__(self, crawler):
        self.logger = crawler.spider.logger

    def load_cookies(self, request):
        cookies = {}

        # Load cookies bytes
        cookie_bytes = request.headers.get("Cookie")

        # Convert cookie byte
        if cookie_bytes is not None:
            cookie_string = cookie_bytes.decode("utf-8")
            cookie_elements = [
                element.strip().split("=") for element in cookie_string.split(";")
            ]
            cookies = {
                element[0]: "=".join(element[1:]) for element in cookie_elements
            }

        return cookies

    def get_cftoken(self, url, delay=5, proxy=None):
        session = cloudscraper.create_scraper(delay=delay)
        request_args = {
            "url": url
        }
        if proxy:
            request_args["proxies"] = {
                "http": proxy,
                "https": proxy
            }

        response = session.get(**request_args)

        user_agent = response.request.headers.get("User-Agent")
        cookies = {
            cookie.name: cookie.value for cookie in response.cookies
        }
        return cookies, user_agent

    def process_response(self, request, response, spider):

        if not self.is_cloudflare_challenge(response):
            return response

        cookies, user_agent = self.get_cftoken(
            request.url,
            proxy=request.meta.get("proxy")
        )

        # Load current cookies
        existing_cookies = self.load_cookies(request)

        # Update existing cookies
        existing_cookies.update(cookies)

        # Replace cookies
        request.cookies = existing_cookies

        # Replace user agent
        request.headers["User-Agent"] = user_agent
        request.dont_filter = True

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
