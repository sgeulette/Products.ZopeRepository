#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This script must be called in a zope instance
# Stéphan Geulette <stephan.geulette@uvcw.be>, UVCW
#

import sys, os, string, shutil
import psycopg2
import logging
logger = logging.getLogger('zope_repository_infos :')

def verbose(*messages):
    logger.info(' '.join(messages))

def error(*messages):
    logger.warn(' '.join(messages))

def trace(*messages):
    if not TRACE:
        return
    logger.debug('TRACE:'+(' '.join(messages)))

pdir = ''
dsn="dbname=zoperepos user=zoperepos password=zopeREP1"
TRACE=True
try:
    #The ZopeRepositoryLocalPassword product can be put in the buildout 'products' subdirectory
    from Products.ZopeRepositoryLocalPassword.config import ZOPEREPOSITORYPASSWORD
    dsn = dsn.replace('zopeREP1', ZOPEREPOSITORYPASSWORD)
except ImportError:
    pass

###############################################################################

def walkInZope(self):
    """ external method called in the zope instance """
    verbose("I'm in Zope : héhé")

    from Products.CMFCore.utils import getToolByName
    from Globals import INSTANCE_HOME

    from Products.ZopeRepository.Extensions.utils import check_zope_admin
    if not check_zope_admin(self):
        return 'walkInZope run with a non admin user: we go out'

    instance = INSTANCE_HOME.rstrip('/')
    # in a buildout, INSTANCE_HOME = xxx/parts/instance
    if instance.endswith('/parts/instance'):
        instance = instance.replace('/parts/instance', '')
    instance = os.path.basename(instance)
    inst_id = getInstanceId(instance)
    if not inst_id:
        return "Instance '%s' not found in database"%instance

    deleteTable('plonesites', "instance_id = %s"%inst_id)

    for objid in self.objectIds(('Plone Site', 'Folder')):
        obj = getattr(self, objid)
        if obj.meta_type == 'Folder':
            for sobjid in obj.objectIds('Plone Site'):
                sobj = getattr(obj, sobjid)
                productsPloneSite(sobj, sobjid, '/' + objid, inst_id)
        elif obj.meta_type == 'Plone Site':
            productsPloneSite(obj, objid, '/', inst_id)
    
    return 'walkInZope finished'

#------------------------------------------------------------------------------

def productsPloneSite(site_obj, plonesite, path, inst_id):
    """ finding in the plone site the installed products """
    #creating plonesites row
    import pdb; pdb.set_trace()
    row = selectOneInTable('plonesites', 'id', "instance_id = %s and plonesite = '%s' and path = '%s'"%(inst_id,plonesite,path))
    if not row and not insertInTable('plonesites', "instance_id, plonesite, path", "%s, '%s', '%s'"%(inst_id, plonesite, path)):
        return

    ps_id = getPlonesiteId(inst_id, plonesite, path)
    deleteTable('plonesites_products', "plonesite_id = %s"%ps_id)

    mountpoint_id = None
    mprow = selectOneInTable('mountpoints', 'id', "instance_id = %s and path = '%s'"%(inst_id,path))
    if mprow:
        mountpoint_id = mprow[0]
    if mountpoint_id and not updateTable('plonesites', "mountpoint_id=%s"%(mountpoint_id), "id = %s"%ps_id):
        return
    
    pqi = getattr(site_obj, 'portal_quickinstaller')
    for aproduct in pqi.listInstalledProducts():
        product_id = getProductId(aproduct['id'])
        insertInTable('plonesites_products', "plonesite_id, product_id, status, errors, installed_version"
            , "%s, %s, '%s', %s, '%s'"%(ps_id, product_id, aproduct['status'], int(aproduct['hasError']), aproduct['installedVersion']))

#------------------------------------------------------------------------------

def getInstanceId(instance):
    row = selectOneInTable('instances', 'id', "instance = '%s'"%instance)
    if row:
        return row[0]
    else:
        error("Cannot find instance '%s' in tables instances"%instance)
    return 0

#------------------------------------------------------------------------------

def getPlonesiteId(inst_id, plonesite, path):
    row = selectOneInTable('plonesites', 'id', "instance_id = %s and plonesite = '%s' and path = '%s'"%(inst_id,plonesite,path))
    if row:
        return row[0]
    else:
        error("Cannot find plonesite '%s/%s' of instance '%s' in plonesites table"%(path, plonesite, inst_id))
    return 0

#------------------------------------------------------------------------------

def getProductId(product):
    row = selectOneInTable('products', 'id', "product = '%s'"%product)
    if row:
        return row[0]
    return 0

#------------------------------------------------------------------------------

def openConnection():
    """ open a postgres connection """
    conn = None
    try:
        #param :: dbname user password
        conn=psycopg2.connect(dsn)
    except Exception, message:
        error("Cannot connect to database %s with dsn '%s'"%(message, dsn))
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
    #verbose("Deletion : %s"%req)
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
