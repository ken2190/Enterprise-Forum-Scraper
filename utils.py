import os
import json
from lxml.html import fromstring


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


def get_html_response(template):
    """
    returns the html response from the `template` contents
    """
    with open(template, 'rb') as f:
        content = f.read()
        html_response = fromstring(content)
        return html_response


def write_json(file_pointer, data):
    """
    writes `data` in file object `file_pointer`.
    """
    json_file = json.dumps(data, indent=4)
    file_pointer.write(json_file)
    file_pointer.write('\n')


def write_comments(file_pointer, comments, output_file):
    """
    writes each comment sequentially in file object `file_pointer`
    """
    comments = sorted(
        comments, key=lambda k: int(k['commentID'])
    )
    # Exclude similar comments (same date,user,id)
    seen = set()
    comments = [
        c for c in comments
        if [(c['commentID'], c['user'], c['date'])
            not in seen, seen.add((
                c['commentID'],
                c['user'],
                c['date']
            ))][0]
    ]

    # If same ids, then update ids
    for index, c in enumerate(comments):
        previous_comments = [cm['commentID'] for cm in comments[:index]]
        if index != 0 and c['commentID'] in previous_comments:
            c['commentID'] = str(int(comments[index-1]['commentID']) + 1)

    for comment in comments:
        write_json(file_pointer, comment)
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
