# -- coding: utf-8 --
import os
import json
import shutil
from lxml.html import fromstring
from lxml.etree import ParserError


class NoAuthor(Exception):
    pass


class NoDate(Exception):
    pass


def handle_error(template, error_folder, error_message):
    """
    If error occured while parsing the `template`,
    write `error_message` with a new filename as `template`
    inside `error_folder`
    """
    if not os.path.exists(error_folder):
        os.makedirs(error_folder)

    file_path = "{}/{}.txt".format(
        error_folder,
        template
    )
    with open(file_path, 'a') as file_pointer:
        file_pointer.write(str(error_message))

def handle_missing_header(template, missing_folder):
    """
    If no author and no date detected while parsing the `template`,
    copy `template` to `missing_folder`
    """
    if not os.path.exists(missing_folder):
        os.makedirs(missing_folder)

    try:
        shutil.copy(template, missing_folder)
    except OSError as err:
        print("ERROR: Failed to copy template to %s directory: %s" % (missing_folder, err))


def get_html_response(template, pattern=None, encoding=None, mode='rb'):
    """
    returns the html response from the `template` contents
    """
    with open(template, mode) as f:
        content = f.read()
        if pattern:
            encoding = encoding if encoding else 'utf-8'
            content = pattern.sub(
                '', content.decode(encoding))\
                .encode(encoding)
        try:
            html_response = fromstring(content)
        except ParserError as ex:
            return
        return html_response

def write_json(file_pointer, data):
    """
    writes `data` in file object `file_pointer`.
    """
    json_file = json.dumps(data, indent=4, ensure_ascii=False)
    file_pointer.write(json_file)
    file_pointer.write('\n')
    
    """
    check if `data` has no `author` and no `date`.
    """
    if not data['_source'].get('author'):
        msg = f'ERROR: Null Author Detected. pid={data["_source"]["pid"]};'
        if data['_source'].get('cid'):
            msg += f' cid={data["_source"]["cid"]};'
        raise NoAuthor(msg)
    elif not data['_source'].get('date'):
        msg = f'ERROR: Date not present. pid={data["_source"]["pid"]};'
        if data['_source'].get('cid'):
            msg += f' cid={data["_source"]["cid"]};'
        raise NoDate(msg)

def write_comments(file_pointer, comments, output_file):
    if not output_file:
        return
    """
    writes each comment sequentially in file object `file_pointer`
    """
    comments = sorted(
        comments, key=lambda k: int(k['_source']['cid'])
    )
    # Exclude similar comments (same date,a,id)
    seen = set()
    comments = [
        c for c in comments
        if [(c['_source']['cid'], c['_source']['author'], c['_source'].get('d'))
            not in seen, seen.add((
                c['_source']['cid'],
                c['_source']['author'],
                c['_source'].get('d')
            ))][0]
    ]

    # If same ids, then update ids
    for index, c in enumerate(comments):
        previous_comments = [cm['_source']['cid'] for cm in comments[:index]]
        if index != 0 and c['_source']['cid'] in previous_comments:
            c['_source']['cid'] = str(int(comments[index-1]['_source']['cid']) + 1)

    for comment in comments:
        write_json(file_pointer, comment)
    file_pointer.close()
    print('\nJson written in {}'.format(output_file))
    print('----------------------------------------\n')


def is_file_final(current_template, template_pattern, files, index):
    """
    checks if the next template is paginated form of
    `current_template`
    """
    try:

        next_template = files[index+1].split('/')[-1]
        match = template_pattern.findall(next_template)
        if not match:
            return True
        if match[0] == current_template:
            return False
        return True
    except:
        return True

def get_decoded_email(email):
    r = int(email[:2],16)
    email = ''.join([
        chr(int(email[i:i+2], 16) ^ r)
        for i in range(2, len(email), 2)])
    return email
