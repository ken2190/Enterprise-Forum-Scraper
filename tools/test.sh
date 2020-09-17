#!/bin/bash

# directory containing output of scraped site (step 1)
OUTPUT_DIR=/data/processing/1

# directory containing output of the parsed JSON files (step 2)
PARSE_DIR=/data/processing/2

# directory containing merged JSON files (step 3)
COMBO_DIR=/data/processing/3

# directory for archives (step 4)
ARCHIVE_DIR=/data/processing/offsite

# directory for JSON to be imported
IMPORT_DIR=/data/processing/import

# jq and rclone binaries
JQ_BIN=jq
RCLONE_BIN=rclone


DATESTAMP=2020-09-01

SITE_NAME=/jqtester.com


CWD=`pwd`
cd $PARSE_DIR/$SITE_NAME
echo "$PARSE_DIR/$SITE_NAME"
$JQ_BIN . *.json -c >> $PARSE_DIR/$SITE_NAME-$DATESTAMP.json
if [ $? -ne 0 ]
then
    echo "ERROR: JQ exited with non-zero exit code"
    cd $CWD
    exit 2
fi

