#!/bin/bash

echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of apache_repository_db"
/srv/python244/bin/python /root/zoperep_scripts/apache_repository_db.py 
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of apache_repository_db"
