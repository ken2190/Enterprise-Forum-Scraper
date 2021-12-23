#!/bin/bash

date=$(date +'%m%d%Y')
echo $date
shodan download --limit -1 elastic-$date.gz "product:mongodb"

