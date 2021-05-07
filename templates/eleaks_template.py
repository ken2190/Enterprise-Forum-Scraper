import re

from .base_template import BaseTemplate


class EleaksParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "eleaks.to"
        self.avatar_name_pattern = re.compile(r'.*/(\w+\.\w+)')
        self.comments_xpath = '//div[@class="message-inner"]'
        self.header_xpath = '//div[@class="message-inner"]'
        self.date_xpath = './/div[contains(@class, "message-attribution-main")]//time/@data-time'
        self.title_xpath = '//h1[@class="p-title-value"]//text()'
        self.post_text_xpath = './/div//div[@class="bbWrapper"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = './/div//div[@class="message-avatar-wrapper"]/a/img/@src'
        self.comment_block_xpath = './/div//header[@class="message-attribution message-attribution--split"]//a/text()'
        self.author_xpath = './/h4[@class="message-name"]/a/span/span/text()|' \
                            './/h4[@class="message-name"]/a/span/text()|' \
                            './/h4[@class="message-name"]/*/text()'

        # main function
        self.main()
