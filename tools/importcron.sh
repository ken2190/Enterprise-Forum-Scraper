#!/usr/bin/env bash

set -e

SCRIPT_PATH="/opt/forumparser/tools/importservice.py"

PROGRAM="$(basename "$0")"
LOGPATH="/var/log/aria/"

if [ -z "$LOGPATH" ]; then
  echo "Usage ./$PROGRAM <path>"
  echo "An importservice.py runner, redirecting runner's stdout and stderr to specified file."
  echo
  echo
  echo "Arguments:"
  echo "  path        Path to the log file, or directory."
  echo "              If path is a directory, logs will be appended to a file in that directory named as \"importservice_<year>-<month>-<day>.log\"."

  exit 1
fi

if [ -d "$LOGPATH" ]; then
  LOGPATH="$(realpath "$LOGPATH")/importservice_$(date +"%Y-%m-%d").log"
fi

echo "Processing Forums"
/usr/bin/env python3 "$SCRIPT_PATH" -type forum >> "$LOGPATH" 2>&1

echo "processing Pastes"
/usr/bin/env python3 "$SCRIPT_PATH" -type paste >> "$LOGPATH" 2>&1

echo "processing NoSQL"
/usr/bin/env python3 "$SCRIPT_PATH" -type nosql >> "$LOGPATH" 2>&1

echo "processing Markets"
/usr/bin/env python3 "$SCRIPT_PATH" -type marketplace >> "$LOGPATH" 2>&1

echo processing "shadownet"
/usr/bin/env python3 "$SCRIPT_PATH" -type shadownet >> "$LOGPATH" 2>&1
