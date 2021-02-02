"""
Error and warning messages
"""

ERROR_MESSAGES = {
    # core errors
    "E00": "Internal error",
    "E01": "Interrupted",

    # site access errors
    "E10": "Site is down",
    "E11": "Access is blocked",
    "E12": "Account is banned",
    "E13": "Login is Failed",

    # forum/productlist errors
    "E20": "No Mainlist found",
    "E21": "No Details found",
    "E22": "No messages found",
    "E23": "Details extraction failed",

    # Captcha failed
    "E30": "Can not bypass captcha"
}

WARNING_MESSAGES = {
    "W01": "Skipped Mainlist",
    "W02": "Skipped Details",
    "W03": "Skipped avatars",
    "W04": "No messages Details",
    "W05": "No Mainlist next pages",
    "W06": "No Details next pages",
    "W07": "Errors in the log",
    "W08": "No new files"
}
