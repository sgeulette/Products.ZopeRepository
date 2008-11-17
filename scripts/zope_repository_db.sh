#!/bin/bash

echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of zope_repository_db" >>zr_db.log
for i in `cat /root/zoperep_scripts/INSTANCES.txt`
do /srv/python244/bin/python /root/zoperep_scripts/zope_repository_db.py -i $i >>zr_db.log 2>&1
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of zope_repository_db" >>zr_db.log
