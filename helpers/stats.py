"""
Scrapy Statistics
"""
from .err_messages import ERROR_MESSAGES, WARNING_MESSAGES


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
    elif finish_reason == 'login_is_failed':
        return _err_msg("E13")
    elif finish_reason == 'cannot_bypass_captcha':
        return _err_msg("E20")

    # NOTE: Check if bypass captcha failed.
    if stats.get('cannot_bypass_captcha', 0) > 1:
        return _err_msg("E20")

    # NOTE: Connected but for unknown reason stopped after few requests.
    if stats.get('retry/max_reached') and stats.get('downloader/request_count', 0) < 20:
        return _err_msg("E10")

    finish_exception = stats.get("finish_exception")
    if finish_exception:
        return "E00", f"{finish_exception[0]}: {finish_exception[1]}"


def get_warnings(stats, site_type='forum'):
    """ Check stats and return list of warnings """
    warnings = []

    # NOTE: Check if no new files
    saved_count = stats.get('mainlist/detail_saved_count', 0)
    if saved_count == 0:
        warnings.append(_warn_msg("W08"))

    return tuple(warnings)
