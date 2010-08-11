#!/bin/bash

echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : Start of apache_repository_db"
/srv/python246/bin/python apache_repository_db.py
echo "## " `date +"%Y-%m-%d, %H:%M:%S"` " : End of apache_repository_db"
