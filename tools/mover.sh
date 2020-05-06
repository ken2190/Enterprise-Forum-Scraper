#!/bin/bash

FOLDER=${1?Error: no folder given}
cd $FOLDER
for i in {10..99}
do
	echo "$i"
	mkdir $i
	mv $i*.json $i/
done
mv *.json 10/
