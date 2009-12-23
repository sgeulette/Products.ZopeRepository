#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# This script must be called in a zope instance
# Stéphan Geulette <stephan.geulette@uvcw.be>, UVCW
#

import sys, os, string, shutil
import socket
import logging
from Products.ZopeRepository.scripts.postgres_utilities import *
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
TRACE=True

###############################################################################

def walkInZope(self):
    """ external method called in the zope instance """
    try:
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

        hostname = socket.gethostname()
        #hostname = '127.0.0.1' # to test if it work with another hostname
        trace("hostname='%s'"%hostname)
        row = selectOneInTable('servers', 'id', "server = '%s'"%hostname)
        server_id = row[0]

        inst_id = getInstanceId(instance, server_id)
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
    except Exception, message:
        return message

#------------------------------------------------------------------------------

def productsPloneSite(site_obj, plonesite, path, inst_id):
    """ finding in the plone site the installed products """
    #creating plonesites row
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

def getInstanceId(instance, server_id):
    row = selectOneInTable('instances', 'id', "instance = '%s' and server_id = %d"%(instance, server_id))
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
