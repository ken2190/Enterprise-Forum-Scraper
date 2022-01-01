#!/bin/bash
YEAR="2022"

rclone copy /data/processing/offsite/2021/paste/ b2:/ViperStorage/pastes/$YEAR/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/2021/shadownet/ b2:/ViperStorage/shadownet/$YEAR/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/2021/forum/ b2:/ViperStorage/forums/$YEAR/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/2021/marketplace/ b2:/ViperStorage/forums/$YEAR/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/2021/meta/ b2:/ViperStorage/meta/$YEAR/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/2021/telegram/ b2:/ViperStorage/telegram/$YEAR/ -v >> /var/log/aria-backup.log
