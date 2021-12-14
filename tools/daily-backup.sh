#!/bin/bash
rclone copy /data/processing/offsite/2021/paste/ b2:/ViperStorage/pastes/2021/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/2021/shadownet/ b2:/ViperStorage/shadownet/2021/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/2021/forum/ b2:/ViperStorage/forums/2021/ -v >> /var/log/aria-backup.log
rclone copy /data/processing/offsite/2021/meta/ b2:/ViperStorage/meta/ -v >> /var/log/aria-backup.log

