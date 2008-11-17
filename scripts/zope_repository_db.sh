#!/bin/bash

echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of zope_repository_db"
for i in `cat /root/zoperep_scripts/INSTANCES.txt`
do /srv/python244/bin/python /root/zoperep_scripts/zope_repository_db.py -i $i
done
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of zope_repository_db"
