# -- coding: utf-8 --
import re
# import locale

from .base_template import BaseTemplate


NOISE_PATTERN = re.compile(r'\<script\>var.*?\</script\>', re.M | re.DOTALL)
TO_DELETE = '<script type="text/javascript" '\
    'src="https://v3rmillion.net/jscripts/myalerts.js"></script>'


def save(file):
    file_name = file.rsplit('/', 1)[1]
    output_path = os.path.join(output_folder, file_name)
    content = open(file, 'r').read()
    formatted_content = NOISE_PATTERN.sub('', content).replace(TO_DELETE, '')
    with open(output_path, 'w') as fp:
        fp.write(formatted_content)
        print(f'Written: {output_path}')


class V3RMillionParser(BaseTemplate):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        self.parser_name = "v3rmillion.net"
        self.thread_name_pattern = re.compile(
            r'(\d+).*html$'
        )
        self.pagination_pattern = re.compile(
            r'\d+-(\d+)\.html$'
        )
        self.avatar_name_pattern = re.compile(r'.*/(\S+\.\w+)')
        self.files = self.get_filtered_files(kwargs.get('files'))
        self.comments_xpath = '//div[@id="posts"]/div[@class="post "]'
        self.header_xpath = '//div[@id="posts"]/div[@class="post "]'
        self.date_xpath = 'div//span[@class="post_date"]/text()'
        self.date_pattern = "%m-%d-%Y, %I:%M %p"
        self.title_xpath = '//span[@class="active"]/text()'
        self.post_text_xpath = 'div//div[@class="post_body scaleimages"]/descendant::text()[not(ancestor::blockquote)]'
        self.avatar_xpath = 'div//div[@class="author_avatar"]/a/img/@src'
        self.comment_block_xpath = 'div[@class="post_head"]/div/strong/a/text()'

        # main function
        self.main()

    def get_filtered_files(self, files):
        filtered_files = list(
            filter(
                lambda x: self.thread_name_pattern.search(
                    x.split('/')[-1]) is not None,
                files
            )
        )
        sorted_files = sorted(
            filtered_files,
            key=lambda x: int(self.thread_name_pattern.search(
                x.split('/')[-1]).group(1)))

        return sorted_files

    def get_author(self, tag):
        author = tag.xpath(
            'div//div[@class="author_information"]/strong/span/a/text()'
        )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]/strong//em/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]/strong//b/span/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]'
                '/strong/span/a/span/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]'
                '/strong/span/a/span/strong/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]'
                '/strong/span/a/span/bold/text()'
            )
        if not author:
            author = tag.xpath(
                'div//div[@class="author_information"]'
                '/strong/span/a/span/strong/s/text()'
            )

        author = author[0].strip() if author else None
        return author

    def get_title(self, tag):
        title = tag.xpath(self.title_xpath)
        title = title[-1].strip() if title else None

        return title
