#!/bin/bash
rm zr_db.log
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of zope_repository_db" >>zr_db.log
for i in `cat INSTANCES.txt`
do /srv/python245/bin/python zope_repository_db.py -i $i >>zr_db.log 2>&1
#  exit;
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of zope_repository_db" >>zr_db.log
