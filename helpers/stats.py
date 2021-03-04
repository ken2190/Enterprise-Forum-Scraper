"""
Scrapy Statistics
"""
from .err_messages import ERROR_MESSAGES, WARNING_MESSAGES

MAINLIST_COUNT = 'mainlist/mainlist_count'
MAINLIST_PROCESSED_COUNT = 'mainlist/mainlist_processed_count'
MAINLIST_NO_DETAIL_COUNT = 'mainlist/mainlist_no_detail_count'
MAINLIST_NEXT_PAGE_COUNT = "mainlist/mainlist_next_page_count"

DETAILS_COUNT = 'mainlist/detail_count'
DETAILS_ALREADY_SCRAPED_COUNT = 'mainlist/detail_already_scraped_count'
DETAILS_OUTDATED_COUNT = 'mainlist/detail_outdated_count'
DETAILS_SAVED_COUNT = 'mainlist/detail_saved_count'
DETAILS_NO_URL_COUNT = 'mainlist/detail_no_url_count'
DETAILS_NO_TOPIC_ID_COUNT = 'mainlist/detail_no_topic_id_count'
DETAILS_NO_DATE_COUNT = 'mainlist/detail_no_date_count'
DETAILS_NO_MESSAGES_COUNT = "mainlist/detail_no_messages_count"
DETAILS_NEXT_PAGE_COUNT = "mainlist/detail_next_page_count"

AVATAR_COUNT = 'mainlist/avatar_count'
AVATAR_SAVED_COUNT = 'mainlist/avatar_saved_count'

CANNOT_BYPASS_CAPTCHA = 'cannot_bypass_captcha'

def _err_msg(code):
    return code, ERROR_MESSAGES[code]


def _warn_msg(code):
    return code, WARNING_MESSAGES[code]


def get_error(stats, site_type='forum'):
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
    elif finish_reason == 'login_is_failed':
        return _err_msg("E13")
    elif finish_reason == 'cannot_bypass_captcha':
        return _err_msg("E20")

    # check if bypass captcha failed
    if stats.get(CANNOT_BYPASS_CAPTCHA, 0) > 1:
        return _err_msg("E20")

    finish_exception = stats.get("finish_exception")
    if finish_exception:
        return "E00", f"{finish_exception[0]}: {finish_exception[1]}"


def get_warnings(stats, site_type='forum'):
    """ Check stats and return list of warnings """

    forum_cnt = stats.get(MAINLIST_COUNT, 0)
    thread_cnt = stats.get(DETAILS_COUNT, 0)
    avatar_cnt = stats.get(AVATAR_COUNT, 0)

    warnings = []

    # check if forum count > 0
    # if stats.get(MAINLIST_COUNT, 0) == 0:
    #     warnings.append(_warn_msg("W10"))

    # check if thread count > 0
    # if stats.get(DETAILS_COUNT, 0) == 0:
    #     warnings.append(_warn_msg("W11"))

    # check if message count > 0
    # if stats.get(DETAILS_NO_MESSAGES_COUNT, 0) >= stats.get(DETAILS_COUNT, 0):
    #     warnings.append(_warn_msg("W12"))

    thread_extraction_failed = (
        stats.get(DETAILS_NO_URL_COUNT, 0) > 0 or
        stats.get(DETAILS_NO_TOPIC_ID_COUNT, 0) > 0 or
        stats.get(DETAILS_NO_DATE_COUNT, 0) > 0
    )
    # if thread_extraction_failed:
    #     warnings.append(_warn_msg("W13"))
        
    # check if all the forums were processed
    processed_forums_cnt = (
        stats.get(MAINLIST_PROCESSED_COUNT, 0) + stats.get(MAINLIST_NO_DETAIL_COUNT, 0)
    )
    # if forum_cnt > processed_forums_cnt:
    #     warnings.append(_warn_msg("W01"))

    # check if all of the threads were processed
    processed_threads_cnt = (
        stats.get(DETAILS_ALREADY_SCRAPED_COUNT, 0) +
        stats.get(DETAILS_OUTDATED_COUNT, 0) +
        stats.get(DETAILS_SAVED_COUNT, 0) +
        stats.get(DETAILS_NO_URL_COUNT, 0) +
        stats.get(DETAILS_NO_TOPIC_ID_COUNT, 0) +
        stats.get(DETAILS_NO_DATE_COUNT, 0) +
        stats.get(DETAILS_NO_MESSAGES_COUNT, 0)
    )
    # if thread_cnt > processed_threads_cnt:
    #     warnings.append(_warn_msg("W02"))

    # check if all avatars were scraped
    # saved_avatars_cnt = stats.get(AVATAR_SAVED_COUNT, 0)
    # if avatar_cnt > saved_avatars_cnt:
    #     warnings.append(_warn_msg("W03"))

    # check if all the threads have messages
    # if stats.get(DETAILS_NO_MESSAGES_COUNT, 0) > 0:
    #     warnings.append(_warn_msg("W04"))

    # check if at least one forum next page found
    # if stats.get(MAINLIST_NEXT_PAGE_COUNT, 0) == 0:
    #     warnings.append(_warn_msg("W05"))

    # check if at least one thread next page found
    # if stats.get(DETAILS_NEXT_PAGE_COUNT, 0) == 0:
    #     warnings.append(_warn_msg("W06"))

    # check for err messages in the log
    # if stats.get("log_count/ERROR", 0) > 0:
    #     warnings.append(_warn_msg("W07"))

    # check if no new files
    saved_count = stats.get(DETAILS_SAVED_COUNT, 0) # + stats.get(AVATAR_SAVED_COUNT, 0)
    if saved_count == 0:
        warnings.append(_warn_msg("W08"))

    return tuple(warnings)
