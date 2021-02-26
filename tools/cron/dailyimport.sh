#!/usr/bin/env bash

set -e

SCRIPT_PATH="/opt/forumparser/tools/importservice.py"

/usr/bin/env python3 "$SCRIPT_PATH" -type forum 2>&1
/usr/bin/env python3 "$SCRIPT_PATH" -type paste 2>&1
