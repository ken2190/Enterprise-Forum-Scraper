"""
Scrapy Statistics
"""
from .err_messages import ERROR_MESSAGES, WARNING_MESSAGES

FORUM_COUNT = 'forum/forum_count'
FORUM_PROCESSED_COUNT = 'forum/forum_processed_count'
FORUM_NO_THREADS_COUNT = 'forum/forum_no_threads_count'
FORUM_NEXT_PAGE_COUNT = "forum/forum_next_page_count"

THREAD_COUNT = 'forum/thread_count'
THREAD_ALREADY_SCRAPED_COUNT = 'forum/thread_already_scraped_count'
THREAD_OUTDATED_COUNT = 'forum/thread_outdated_count'
THREAD_SAVED_COUNT = 'forum/thread_saved_count'
THREAD_NO_URL_COUNT = 'forum/thread_no_url_count'
THREAD_NO_TOPIC_ID_COUNT = 'forum/thread_no_topic_id_count'
THREAD_NO_DATE_COUNT = 'forum/thread_no_date_count'
THREAD_NO_MESSAGES_COUNT = "forum/thread_no_messages_count"
THREAD_NEXT_PAGE_COUNT = "forum/thread_next_page_count"

AVATAR_COUNT = 'forum/avatar_count'
AVATAR_SAVED_COUNT = 'forum/avatar_saved_count'


def _err_msg(code):
    return code, ERROR_MESSAGES[code]


def _warn_msg(code):
    return code, WARNING_MESSAGES[code]


def get_error(stats):
    finish_reason = stats.get('finish_reason')
    if finish_reason == 'closespider_errorcount':
        return _err_msg("E00")
    elif finish_reason == 'shutdown':
        return _err_msg("E01")
    elif finish_reason == 'site_is_down':
        return _err_msg("E10")
    elif finish_reason == 'access_is_blocked':
        return _err_msg("E11")
    elif finish_reason == 'account_is_banned':
        return _err_msg("E12")

    # check if forum count > 0
    if stats.get(FORUM_COUNT, 0) == 0:
        return _err_msg("E20")

    # check if thread count > 0
    if stats.get(THREAD_COUNT, 0) == 0:
        return _err_msg("E21")

    # check if message count > 0
    if stats.get(THREAD_NO_MESSAGES_COUNT, 0) >= stats.get(THREAD_COUNT, 0):
        return _err_msg("E22")

    thread_extraction_failed = (
        stats.get(THREAD_NO_URL_COUNT, 0) > 0 or
        stats.get(THREAD_NO_TOPIC_ID_COUNT, 0) > 0 or
        stats.get(THREAD_NO_DATE_COUNT, 0) > 0
    )
    if thread_extraction_failed:
        return _err_msg("E23")


def get_warnings(stats):
    """ Check stats and return list of warnings """

    forum_cnt = stats.get(FORUM_COUNT, 0)
    thread_cnt = stats.get(THREAD_COUNT, 0)
    avatar_cnt = stats.get(AVATAR_COUNT, 0)

    warnings = []

    # check if all the forums were processed
    processed_forums_cnt = (
        stats.get(FORUM_PROCESSED_COUNT, 0) + stats.get(FORUM_NO_THREADS_COUNT, 0)
    )
    if forum_cnt > processed_forums_cnt:
        warnings.append(_warn_msg("W01"))

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
        warnings.append(_warn_msg("W02"))

    # check if all avatars were scraped
    saved_avatars_cnt = stats.get(AVATAR_SAVED_COUNT, 0)
    if avatar_cnt > saved_avatars_cnt:
        warnings.append(_warn_msg("W03"))

    # check if all the threads have messages
    if stats.get(THREAD_NO_MESSAGES_COUNT, 0) > 0:
        warnings.append(_warn_msg("W04"))

    # check if at least one forum next page found
    if stats.get(FORUM_NEXT_PAGE_COUNT, 0) == 0:
        warnings.append(_warn_msg("W05"))

    # check if at least one thread next page found
    if stats.get(THREAD_NEXT_PAGE_COUNT, 0) == 0:
        warnings.append(_warn_msg("W06"))

    # check for err messages in the log
    if stats.get("log_count/ERROR", 0) > 0:
        warnings.append(_warn_msg("W07"))

    # check if no new files
    saved_count = stats.get(THREAD_SAVED_COUNT, 0) + stats.get(AVATAR_SAVED_COUNT, 0)
    if saved_count == 0:
        warnings.append(_warn_msg("W08"))

    return tuple(warnings)
