import re

from .base_template import BaseTemplate


class RutorParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "rutor_rutorzzmfflzllk5"
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.comments_xpath = '//article[contains(@class,"message--post")]'
        self.header_xpath = '//article[contains(@class,"message--post")]'
        self.title_xpath = '//h1[@class="p-title-value"]//text()'
        self.date_xpath = './/time//text()'
        self.author_xpath = './/div[@class="message-userDetails"]/h4/a//text()'
        self.post_text_xpath = './/article[contains(@class,"selectToQuote")]'\
                               '/descendant::text()[not(ancestor::div[conta'\
                               'ins(@class,"bbCodeBlock--quote")])]'
        self.avatar_xpath = './/div[@class="message-avatar "]//img/@src'
        self.comment_block_xpath = './/ul[contains(@class,"message-attribution-opposite")]/li[2]/a/text()'

        # main function
        self.main()
