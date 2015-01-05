#!/bin/bash
if [ -e zr_db.log ]; then
   rm zr_db.log
fi
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of zope_repository_db" >>zr_db.log
for i in `cat INSTANCES.txt`
do /srv/python246/bin/python zope_repository_db.py -i $i >>zr_db.log 2>&1
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of zope_repository_db" >>zr_db.log
