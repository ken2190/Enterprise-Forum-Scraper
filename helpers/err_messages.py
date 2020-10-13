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

    # forum errors
    "E20": "No forums found",
    "E21": "No threads found",
    "E22": "No messages found",
    "E23": "Thread extraction failed"
}

WARNING_MESSAGES = {
    "W01": "Skipped forums",
    "W02": "Skipped threads",
    "W03": "Skipped avatars",
    "W04": "No messages thread",
    "W05": "No forum next pages",
    "W06": "No thread next pages",
    "W07": "Errors in the log",
    "W08": "No new files",    
}
