"""
Scrapy Statistics
"""

FORUM_COUNT = 'forum/forum_count'
FORUM_PROCESSED_COUNT = 'forum/forum_processed_count'
FORUM_NO_THREADS_COUNT = 'forum/forum_no_threads_count'

THREAD_COUNT = 'forum/thread_count'
THREAD_ALREADY_SCRAPED_COUNT = 'forum/thread_already_scraped_count'
THREAD_OUTDATED_COUNT = 'forum/thread_outdated_count'
THREAD_SAVED_COUNT = 'forum/thread_saved_count'
THREAD_NO_URL_COUNT = 'forum/thread_no_url_count'
THREAD_NO_TOPIC_ID_COUNT = 'forum/thread_no_topic_id_count'
THREAD_NO_DATE_COUNT = 'forum/thread_no_date_count'
THREAD_NO_MESSAGES_COUNT = "forum/thread_no_messages_count"

AVATAR_COUNT = 'forum/avatar_count'
AVATAR_SAVED_COUNT = 'forum/avatar_saved_count'


def get_warnings(stats):
    """ Check stats and return list of warnings """

    # disable checks if no base stats
    # good_stats = (FORUM_COUNT in stats) and (THREAD_COUNT in stats) and (AVATAR_COUNT in stats)
    # if not good_stats:
        # return

    forum_cnt = stats.get(FORUM_COUNT, 0)
    thread_cnt = stats.get(THREAD_COUNT, 0)
    avatar_cnt = stats.get(AVATAR_COUNT, 0)

    warnings = []

    if stats.get('finish_reason') == 'shutdown':
        warnings.append('The scraping process was interrupted by the user!')

    # check if at least one forum was found
    if forum_cnt == 0:
        warnings.append('No forums found on the main page!')

    # check if all the forums were processed
    processed_forums_cnt = (
        stats.get(FORUM_PROCESSED_COUNT, 0) + stats.get(FORUM_NO_THREADS_COUNT, 0)
    )
    if forum_cnt > processed_forums_cnt:
        warnings.append(
            f'Only {processed_forums_cnt} forums out of {forum_cnt} were processed!'
        )

    # check if at least one forum has a thread
    if forum_cnt == stats.get(FORUM_NO_THREADS_COUNT, 0):
        warnings.append('All of the forums do not contain any thread!')

    # check if at least one thread was processed
    if thread_cnt == 0:
        warnings.append('No threads found!')

    # check if all of the threads were processed
    processed_threads_cnt = (
        stats.get(THREAD_ALREADY_SCRAPED_COUNT, 0) +
        stats.get(THREAD_OUTDATED_COUNT, 0) +
        stats.get(THREAD_SAVED_COUNT, 0) +
        stats.get(THREAD_NO_URL_COUNT, 0) +
        stats.get(THREAD_NO_TOPIC_ID_COUNT, 0) +
        stats.get(THREAD_NO_DATE_COUNT, 0) +
        stats.get(THREAD_NO_MESSAGES_COUNT, 0)
    )
    if thread_cnt > processed_threads_cnt:
        warnings.append(
            f'Not all of the threads were processed ({processed_threads_cnt} out of '
            f'{thread_cnt})!'
        )

    # check if all the threads have URLs
    if stats.get(THREAD_NO_URL_COUNT, 0) > 0:
        warnings.append(
            f'URL not found for {stats.get(THREAD_NO_URL_COUNT, 0)} threads!'
        )

    # check if all the threads have topic IDs
    if stats.get(THREAD_NO_TOPIC_ID_COUNT, 0) > 0:
        warnings.append(
            f'Topic ID not found for {stats.get(THREAD_NO_TOPIC_ID_COUNT, 0)} threads!'
        )

    # check if all the threads have last dates
    if stats.get(THREAD_NO_DATE_COUNT, 0) > 0:
        warnings.append(
            f'The last date not found for {stats.get(THREAD_NO_DATE_COUNT, 0)} threads!'
        )

    # check if all the threads have messages
    if stats.get(THREAD_NO_MESSAGES_COUNT, 0) > 0:
        warnings.append(
            f'No messages found in {stats.get(THREAD_NO_MESSAGES_COUNT, 0)} threads!'
        )

    # check if all avatars were scraped
    saved_avatars_cnt = stats.get(AVATAR_SAVED_COUNT, 0)
    if avatar_cnt > saved_avatars_cnt:
        warnings.append(
            f'Only {saved_avatars_cnt} avatar out of {avatar_cnt} scraped!'
        )

    return tuple(warnings)
