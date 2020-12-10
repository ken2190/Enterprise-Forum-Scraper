import re
from .base_template import BaseTemplate


class MajesticGardenParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "majestic garden"
        self.avatar_name_pattern = re.compile(r"attach=(\d+)")
        self.comments_xpath = '//div[contains(@class,"windowbg")]'
        self.header_xpath = '//div[contains(@class,"windowbg")]'
        self.date_xpath = './/div[@class="postarea"]//div[@class="keyinfo"]//div[@class="smalltext"]/text()[2]'
        self.author_xpath = './/div[@class="poster"]/h4//text()'
        self.post_text_xpath = './/div[@class="post"]/div/text()'
        self.avatar_xpath = './/img[@class="avatar"]/@src'
        self.title_xpath = '//h3[@class="catbg"]/text()'
        self.index = 1
        self.avatar_ext = 'jpg'

        # main function
        self.main()

    def get_title(self, tag):
        title_blocks = tag.xpath(self.title_xpath)
        title = ''.join(title_blocks)
        title = title.split("Topic:")[1].strip().split("(")[0]
        title = title.strip().split(']')[-1] if title else None
        return title
