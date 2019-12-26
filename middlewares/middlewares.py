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
        if not session:
            session = uuid.uuid1().hex

        request.meta["proxy"] = self.super_proxy_url % (
            self.username,
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
