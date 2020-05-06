#!/bin/bash

folder=$1

rsync -avz -e 'ssh -i ~/.ssh/avatarkey.pem' --rsync-path="mkdir -p /var/www/dataviper/images/avatars/$1/ && rsync" $folder/ root@174.138.43.247:/var/www/dataviper/images/avatars/$1
