# -- coding: utf-8 --
import re

from .base_template import BaseTemplate


class BlackBankParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parser_name = "blackbank market"
        self.thread_name_pattern = re.compile(r'viewtopic\.php.*id=(\d+)')
        self.files =self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="brdmain"]/div[contains(@class,"blockpost")]'
        self.header_xpath = '//div[@id="brdmain"]/div[contains(@class,"blockpost")]'
        self.date_xpath = 'h2//span[@class="conr"]/following-sibling::a[1]/text()'
        self.date_pattern = "%Y-%m-%d %H:%M:%S"
        self.author_xpath =  'div//dt/strong/text()'
        self.title_xpath = 'div//div[@class="postright"]/h3/text()'
        self.post_text_xpath =  'div//div[@class="postmsg"]/*/text()'
        self.comment_block_xpath =  'h2//span[@class="conr"]/text()'

        # main function
        self.main()

    def get_pid(self):
        pid_pattern = re.compile(r'id=(\d+)')
        pid = pid_pattern.findall(self.thread_id)
        pid = pid[0] if pid else self.thread_id

        return pid
