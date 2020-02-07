#!/bin/bash

FOLDER=${1?Error: no folder given}
cd $FOLDER
for i in {10..99}
do
	jq . $i/*.json -c >> $i.json
done

echo "combine all remaining json files into one"

cat *.json >> ../../import/$FOLDER.json
