#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# postgresql utility methods
# Stéphan Geulette <stephan.geulette@uvcw.be>, UVCW
#

import sys, os
import psycopg2

def verbose(*messages):
    print '>>', ' '.join(messages)
def error(*messages):
    print '!!', (' '.join(messages))
def trace(*messages):
    if not TRACE:
        return
    print 'TRACE:', ' '.join(messages)

TRACE = False

#dsn="host=localhost port=5432 dbname=zoperepos user=zoperepos password=zopeREP1"
dsn="host=localhost dbname=zoperepos user=zoperepos password=zopeREP1"

try:
    #The ZopeRepositoryLocalPassword product can be put in the buildout 'products' subdirectory
    from Products.ZopeRepositoryLocalPassword.config import *
    dsn = dsn.replace('zopeREP1', ZOPEREPOSITORYPASSWORD)
    dsn = dsn.replace('localhost', ZOPEREPOSITORYHOST)
except (ImportError, NameError):
    pass

#------------------------------------------------------------------------------

def openConnection():
    """ open a postgres connection """
    conn = None
    try:
        #param :: dbname user password
        conn=psycopg2.connect(dsn)
    except Exception, message:
        msg = "Cannot connect to database with dsn '%s': %s"%(dsn, message)
        error(msg)
        raise Exception(msg)
    return conn

#------------------------------------------------------------------------------

def insertInTable(table, columns, vals):
    """ insert values in a table """
    conn = openConnection()
    cursor = conn.cursor()
    req="insert into %s(%s) \
                values(%s)"%(table, columns, vals)
#    verbose("Insertion : %s"%req)
    try:
        cursor.execute(req)
    except Exception, message:
        error("Cannot insert in database : %s"%message)
        error("Request was : '%s'"%req)
        conn.close()
        return False
    conn.commit()
    conn.close()
    return True

#------------------------------------------------------------------------------

def updateTable(table, updates, condition=''):
    """ update columns in a table """
    conn = openConnection()
    cursor = conn.cursor()
    req="update %s set %s"%(table, updates)
    if condition:
        req += ' where %s'%condition
#    verbose("Update : %s"%req)
    try:
        cursor.execute(req)
    except Exception, message:
        error("Cannot update in database : %s"%message)
        error("Request was : '%s'"%req)
        conn.close()
        return False
    conn.commit()
    conn.close()
    return True

#------------------------------------------------------------------------------

def selectAllInTable(table, selection, condition=''):
    """ select multiple lines in a table """
    conn = openConnection()
    cursor = conn.cursor()
    req="select %s from %s"%(selection, table)
    if condition:
        req += ' where %s'%condition
#    verbose("Selection : %s"%req)
    try:
        cursor.execute(req)
        data = cursor.fetchall()
    except Exception, message:
        error("Cannot select from database : %s"%message)
        error("Request was : '%s'"%req)
        conn.close()
        return None
    conn.close()
    return data

#------------------------------------------------------------------------------

def selectOneInTable(table, selection, condition=''):
    """ select a single line in a table """
    conn = openConnection()
    cursor = conn.cursor()
    req="select %s from %s"%(selection, table)
    if condition:
        req += ' where %s'%condition
#    verbose("Selection : %s"%req)
    try:
        cursor.execute(req)
        data = cursor.fetchone()
    except Exception, message:
        error("Cannot select from database : %s"%message)
        error("Request was : '%s'"%req)
        conn.close()
        return None
    conn.close()
    return data

#------------------------------------------------------------------------------

def deleteTable(table, condition=''):
    """ delete a table """
    conn = openConnection()
    cursor = conn.cursor()
    req="delete from %s"%(table)
    if condition:
        req += ' where %s'%condition
    trace("Deletion : %s"%req)
    try:
        cursor.execute(req)
    except Exception, message:
        error("Cannot delete from database : %s"%message)
        error("Request was : '%s'"%req)
        conn.close()
        return False
    conn.commit()
    conn.close()
    return True

#------------------------------------------------------------------------------

def runCommand(cmd):
    """ run an os command and get back the stdout and stderr outputs """
    ret = os.system(cmd + ' >_cmd_pv.out 2>_cmd_pv.err')
    stdout = stderr = []
    try:
        if os.path.exists('_cmd_pv.out'):
            ofile = open( '_cmd_pv.out', 'r')
            stdout = ofile.readlines()
            ofile.close()
            os.remove('_cmd_pv.out')
        else:
            error("File %s does not exist" % '_cmd_pv.out')
    except IOError:
        error("Cannot open %s file" % '_cmd_pv.out')
    try:
        if os.path.exists('_cmd_pv.err'):
            ifile = open( '_cmd_pv.err', 'r')
            stderr = ifile.readlines()
            ifile.close()
            os.remove('_cmd_pv.err')
        else:
            error("File %s does not exist" % '_cmd_pv.err')
    except IOError:
        error("Cannot open %s file" % '_cmd_pv.err')
    return( stdout,stderr )

#------------------------------------------------------------------------------

#problem with big output : subprocess is frozen
def runCommand2(cmd):
    (child_stdin, child_stdout, child_stderr) = os.popen3(cmd, 't', 1000000)
    stderr = child_stderr.readlines()
    child_stderr.close()
    stdout = child_stdout.readlines()
    child_stdout.close()
    child_stdin.close()
    return( stdout,stderr )

#------------------------------------------------------------------------------
