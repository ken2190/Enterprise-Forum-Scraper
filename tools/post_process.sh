#!/bin/bash

# input arguments
SITE_NAME=${1?Error: no site name provided}
DATESTAMP=${2?Error: no datestamp provided}

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

if [ ! -d $OUTPUT_DIR ]
then
    echo "ERROR: Scraper output directory does not exist $OUTPUT_DIR"
    exit 2
fi

if [ ! -d $PARSE_DIR ]
then
    echo "ERROR: Parsing output directory does not exist $PARSE_DIR"
    exit 2
fi

if [ ! -d $COMBO_DIR ]
then
    echo "ERROR: JSON combo directory does not exist $COMBO_DIR"
    exit 2
fi

if [ ! -d $ARCHIVE_DIR ]
then
    echo "ERROR: Archive directory does not exist $ARCHIVE_DIR"
    exit 2
fi

if [ ! -d $IMPORT_DIR ]
then
    echo "ERROR: Import directory does not exist $IMPORT_DIR"
    exit 2
fi

# offsite destination of archive files
OFFSITE_DEST=b2:/ViperStorage/datadumps/

# jq and rclone binaries
JQ_BIN=jq
RCLONE_BIN=rclone

##############################################
# merge parsed files
##############################################
CWD=`pwd`
cd $PARSE_DIR/$SITE_NAME
$JQ_BIN . *.json -c >> $COMBO_DIR/$SITE_NAME-$DATESTAMP.json
if [ $? -ne 0 ]
then
    echo "ERROR: JQ exited with non-zero exit code"
    cd $CWD
    exit 2
fi
cd $CWD

##############################################
# archive scraped HTML and combined JSON
##############################################
tar -cvzf $ARCHIVE_DIR/original/$SITE_NAME-html-$DATESTAMP.tar.gz $OUTPUT_DIR/$SITE_NAME/
if [ $? -ne 0 ]
then
    echo "ERROR: Failed to create HTML archive"
    exit 2
fi

tar -cvzf  $ARCHIVE_DIR/$SITE_NAME-$DATESTAMP.tar.gz $COMBO_DIR/$SITE_NAME-$DATESTAMP.json
if [ $? -ne 0 ]
then
    echo "ERROR: Failed to create JSON archive"
    exit 2
fi

##############################################
# move combined JSON to import dir
##############################################
mv $COMBO_DIR/$SITE_NAME-$DATESTAMP.json $IMPORT_DIR/
if [ $? -ne 0 ]
then
    echo "ERROR: Failed to move JSON to import directory"
    exit 2
fi

##############################################
# delete scraped HTML and parsed JSON files
##############################################

# check if archive file exists and not 0 bytes
if [ -f "$ARCHIVE_DIR/original/$SITE_NAME-html-$DATESTAMP.tar.gz" ] && 
   [ -s "$ARCHIVE_DIR/original/$SITE_NAME-html-$DATESTAMP.tar.gz" ]
then
    rm -rf $OUTPUT_DIR/$SITE_NAME
    rm -rf $PARSE_DIR/$SITE_NAME
else
    echo "WARNING: missing or empty archive file $ARCHIVE_DIR/original/$SITE_NAME-html-$DATESTAMP.tar.gz"
    exit 2
fi

##############################################
# send archives offset
##############################################
rclone copy $ARCHIVE_DIR/ $OFFSITE_DEST -v
if [ $? -ne 0 ]
then
    echo "ERROR: Failed to copy archive directory offset"
    exit 2
fi
