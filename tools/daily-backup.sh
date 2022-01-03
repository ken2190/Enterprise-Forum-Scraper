#!/bin/bash
YEAR="2022"

rclone copy /data/processing/offsite/$YEAR/paste/ b2:/ViperStorage/pastes/$YEAR/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/$YEAR/shadownet/ b2:/ViperStorage/shadownet/$YEAR/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/$YEAR/forum/ b2:/ViperStorage/forums/$YEAR/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/$YEAR/marketplace/ b2:/ViperStorage/forums/$YEAR/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/$YEAR/meta/ b2:/ViperStorage/meta/$YEAR/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/$YEAR/telegram/ b2:/ViperStorage/telegram/$YEAR/ -v >> /var/log/aria-backup.log
