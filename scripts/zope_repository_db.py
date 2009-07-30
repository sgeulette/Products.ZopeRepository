#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Script to create and update a repository on zope instances
# Stéphan Geulette <stephan.geulette@uvcw.be>, UVCW
#

import sys, os, commands, string, re, shutil
import psycopg2
import urllib
from datetime import datetime, timedelta
import socket

def verbose(*messages):
    print '>>', ' '.join(messages)
def error(*messages):
    print '!!', (' '.join(messages))
def trace(*messages):
    if not TRACE:
        return
    print 'TRACE:', ' '.join(messages)

buildout_inst_type = None #True for buildout, False for manual instance
tempdir = ''
now = datetime(1973,02,12).now()
pfolders = {}
temp_added = False
dsn="dbname=zoperepos user=zoperepos password=zopeREP1"
ext_method = 'zope_repository_infos'
ext_filename = 'zope_infos.py'
function = 'walkInZope'
TRACE = False

###############################################################################

def main():
    global instdir, tempdir, buildout_inst_type

#    import pdb; pdb.set_trace()
    instdir = instdir.rstrip('/')
    verbose("Working on instance %s" % instdir)

    # Finding the instance type (buildout or manual)
    if os.path.exists(os.path.join(instdir,'parts')):
        buildout_inst_type = True
        verbose("\tInstance is a buildout !")
    elif os.path.exists(os.path.join(instdir,'etc')):
        buildout_inst_type = False
        verbose("\tInstance is a manual installation !")
    elif not os.path.exists(instdir) or True:
        error("! Invalid instance path '%s' or instance type not detected"%instdir)
        sys.exit(1)

    if buildout_inst_type:
        zodbfilename = os.path.join(instdir, 'parts/instance/etc/zope.conf')
        zopectlfilename = os.path.join(instdir, 'parts/instance/bin/zopectl')
        fspath = os.path.join(instdir, 'var/filestorage/')
        inst_type = 'buildout'
        productsdir = os.path.join(instdir, 'parts/omelette/Products')
    else:
        zodbfilename = os.path.join(instdir, 'etc/zope.conf')
        zopectlfilename = os.path.join(instdir, 'bin/zopectl')
        fspath = os.path.join(instdir, 'var/')
        inst_type = 'manual'
        productsdir = os.path.join(instdir, 'Products')

    instance = os.path.basename(instdir)
    if not tempdir:
        tempdir = os.path.join(instdir, 'temp')
    hostname = socket.gethostname()

    trace("host='%s', inst='%s', zodbf='%s', zopectlf='%s', fspath='%s', products='%s'"
        %(hostname, instance, zodbfilename, zopectlfilename, fspath, productsdir))

    #deletion of table instances if the older record is >23h, as the script is run on all instances each night
    #needed to delete obsolete instances
    row = selectOneInTable('instances', 'min(creationdate)')
    if row[0] and (now - row[0]) > timedelta(hours=3):
#    if row[0] and (now - row[0]) > timedelta(minutes=8):
#    if True:
        deleteTable('instances')
        deleteTable('servers')
        deleteTable('products')
        deleteTable('instances_products')
        deleteTable('plonesites')
        deleteTable('plonesites_products')
        deleteTable('mountpoints')

    #Creation or update of the instance information
    row = selectOneInTable('servers', '*', "server = '%s'"%hostname)
    if not row and not insertInTable('servers', "server, ip_address", "'%s', '%s'"
                %(hostname, socket.gethostbyname(hostname))):
        sys.exit(1)
    server_id = getServerId()

    #Creation or update of the instance information
    row = selectOneInTable('instances', '*', "instance = '%s'"%instance)
    if row:
        if not updateTable('instances', "creationdate='%s'"%(now), "id = %s"%row[0]):
            sys.exit(1)
        if not updateTable('instances', "type='%s'"%(inst_type), "id = %s"%row[0]):
            sys.exit(1)
        deleteTable('instances_products', "instance_id = %s"%row[0])
        deleteTable('plonesites', "instance_id = %s"%row[0])
        deleteTable('mountpoints', "instance_id = %s"%row[0])
    elif not insertInTable('instances', "instance, creationdate, type, server_id", "'%s', '%s', '%s', %s"
                %(instance, now, inst_type, server_id)):
        sys.exit(1)

    inst_id = getInstanceId(instance)

    # Getting some informations in zopectl file (zope path, zope version)
    read_zopectlfile(zopectlfilename, inst_id)

    # Getting some informations in zope.conf file (port, mount points)
    port = treat_zopeconflines(zodbfilename, fspath, inst_id)

    # Getting products in a list
    readProductsDir(productsdir, pfolders)

#    input('Press a key to continue')
#    return
    verbose("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"
        %('Product', 'Local version', 'Rep version', 'Local rev', 'Rep rev', 'Diff flag', 'Rep url', 'Diff lines', 'Diff count'))

    fkeys = pfolders.keys()
    fkeys.sort()
    for product in fkeys:
#        if product != 'BelgianEidAuthPlugin':
#            continue
        local_version = None
        local_rev = None
        rep_url = None
        rep_version = None
        rep_rev = None
        diff_flag = None
        diff_lines = []
        diff_count = 0

        trace("Current product %s"%product)
        os.chdir(pfolders[product])

        #Getting local version in version.txt
        local_version = getLocalVersion(pfolders[product])
        trace("local version=%s"%local_version)

        #Testing if product is svn linked
        is_svn = True
        svn_cmd = 'svn info'
        (svn_out, svn_err) = runCommand(svn_cmd)
        if svn_err:
            if svn_err[0].startswith("svn: '.' "):
                is_svn = False
                pass
            else:
                error("error running command %s : %s" % (svn_cmd, ''.join(svn_err)))
        elif svn_out:
            #trace('output=%s'%"".join(svn_out))
            #Getting svn repository url
            rep_url = svn_out[1].strip('\n ')
            if rep_url.startswith('URL'):
                rep_url = rep_url[3:].strip(' :')
                trace("svn URL = '%s'"%rep_url)
            else:
                error("URL not matched : '%s'"%rep_url)
            if not (rep_url.startswith('http://') or rep_url.startswith('https://')):
                error("URL not beginning by http(s):// : '%s'"%rep_url)
            #Getting local repository version
            local_rev = getRevision(svn_out)
            trace("Local revision = %s"%local_rev)
        else:
            error('No output for command%s'%svn_cmd)

        if is_svn:
            (rep_version, rep_rev) = getRepositoryVersion(rep_url, product)
            #dir was changed in getRepositoryVersion()
            os.chdir(pfolders[product])
#            if product in ('PloneHelpCenter', 'PloneSoftwareCenter', 'urban'):
#                diff_flag = 'Skipped'
#            elif local_rev != rep_rev or local_rev == '-':
            if local_rev != rep_rev or not local_rev or not rep_rev:
#                verbose('Running svn diff')
                diff_cmd = 'svn diff -r HEAD'
                (diff_out, diff_err) = runCommand(diff_cmd)
                if diff_err:
                    error("error running command %s : %s" % (diff_cmd, ''.join(diff_err)))
                elif diff_out:
                    diff_flag = 'Yes'
                    diff_lines = diff_out
                    diff_count = len(diff_out)
#                    verbose('output=%s'%"".join(diff_out))
                else:
                    diff_flag = 'No'

        trace("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"
            %(product, local_version, rep_version, local_rev, rep_rev, diff_flag, rep_url, diff_lines, diff_count))
        diff_lines_to_print = diff_lines
        if diff_lines_to_print:
            diff_lines_to_print = 'too long'
        verbose("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"
            %(product, local_version, rep_version, local_rev, rep_rev, diff_flag, rep_url, diff_lines_to_print, diff_count))
        insertInstancesProducts(instance, product, local_version, rep_version, local_rev, rep_rev, diff_flag, rep_url, diff_lines, diff_count)

    product_id = getProductId('CMFPlone')
    if product_id:
        row = selectOneInTable('instances_products', 'local_version', "instance_id = %s and product_id = %s"%(inst_id, product_id))
        if row:
            updateTable('instances', "plone_version='%s'"%(row[0]), "id = %s"%inst_id)

    if temp_added:
        shutil.rmtree(tempdir)

    #copying extensions script
    #NO MORE NEEDED : the script is present in ZopeRepository products
#     ext_file = os.path.join(instdir, 'Extensions', ext_filename)
#     if not os.path.exists(ext_file):
#         this_script_dir = os.path.dirname(sys.argv[0])
#         try:
#             shutil.copyfile(os.path.join(this_script_dir, 'Extensions', ext_filename) , ext_file)
#             verbose( "'%s' copied to '%s'" % (ext_filename, ext_file))
#         except Exception, errmsg:
#             error( "'%s' NOT COPIED to '%s'" % (ext_filename, ext_file))
#             error(str(errmsg))
#             sys.exit(1)

    #creating and calling external method in zope
    host = "http://localhost:%s" % port
    urllib._urlopener = MyUrlOpener()
    url_pv = "%s/%s" % (host, ext_method)
    current_url = url_pv
    try:
        verbose("Running '%s'"%current_url)
        ret_html = urllib.urlopen(current_url).read()
        if 'the requested resource does not exist' in ret_html:
            verbose('external method %s not exist : we will create it'%ext_method)
            (module, extension) = os.path.splitext(ext_filename)
            module = 'ZopeRepository.' + module
            current_url = "%s/manage_addProduct/ExternalMethod/manage_addExternalMethod?id=%s&module=%s&function=%s&title="%(host, ext_method, module, function)
            verbose("Running now '%s'"%current_url)
            ret_html = urllib.urlopen(current_url).read()
            if 'the requested resource does not exist' in ret_html or \
                ('The specified module' in ret_html and "couldn't be found" in ret_html):
                error("Cannot create external method in zope : '%s'"%ret_html)
                sys.exit(1)
            else:
                current_url = "%s/%s/valid_roles" % (host, ext_method)
                verbose("Running now '%s'"%current_url)
                ret_html = urllib.urlopen(current_url).read()
                if not ret_html[0] == '(':
                    error("error with valid_roles return: '%s'"%ret_html)
                    sys.exit(1)
                valid_roles = list(eval(ret_html))
                managerindex = valid_roles.index('Manager')
                current_url = "%s/%s/permission_settings" % (host, ext_method)
                verbose("Running now '%s'"%current_url)
                ret_html = urllib.urlopen(current_url).read()
                if not ret_html[0] == '[':
                    error("error with permission_settings return: '%s'"%ret_html)
                    sys.exit(1)
                permission_settings = eval(ret_html)
                params = {}
                count = 0
                for perm in permission_settings:
                    if perm['name'] in ('Access contents information','View'):
                        params['p%dr%d'%(count,managerindex)] = 'on'
                    else:
                        params['a%d'%count] = 'on'
                    count += 1
                current_url = "%s/%s/manage_changePermissions" % (host, ext_method)
                verbose("Running now '%s'"%current_url)
# params example                       params = {  'permission_to_manage':'View', 
#                                    'roles':['Manager'], }
                data = urllib.urlencode(params)
                ret_html = urllib.urlopen(current_url, data).read()
                if 'Your changes have been saved' not in ret_html:
                    error("Error changing permissions with URL '%s', data '%s'" % (current_url,str(data)))
                    sys.exit(1)
                current_url = url_pv
                verbose("Running again '%s'"%current_url)
                ret_html = urllib.urlopen(current_url).read()
        verbose("zope_infos ='%s'"%ret_html)
    except Exception, msg:
        error("Cannot open URL %s, aborting: '%s'" % (current_url,msg))
        sys.exit(1)

#------------------------------------------------------------------------------

class MyUrlOpener(urllib.FancyURLopener):
    """ redefinition of this class to give the user and password"""
    def prompt_user_passwd(self, host, realm):
        return (user,pwd)
    def __init__(self, *args):
        self.version = "Zope Packer"
        urllib.FancyURLopener.__init__(self, *args)

#------------------------------------------------------------------------------

def readProductsDir(pdir, dic):
    """ Read the products dir and save the folder names in a dic """
    if not os.path.exists(pdir):
        error("Dir products '%s' doesn't exist"%pdir)
        return 
    for (dirname, path) in getSubdirs(pdir):
        dic[dirname] = path
    trace(str(dic))

#------------------------------------------------------------------------------

def getSubdirs(dirpath):
    """ Read the dir and return the folders """
    folders = []
    for filename in os.listdir(dirpath):
        filepath = os.path.join(dirpath, filename)
        if os.path.isdir(filepath):
            folders.append((filename, os.path.realpath(filepath)))
    return folders

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

def getLocalVersion(product_dir):
    """ get the version in version.txt or metadata.xml file """ 
    txt_version = xml_version = ''
    file_name = os.path.join(product_dir, 'version.txt')
    if os.path.exists(file_name):
        command = 'pg '+file_name
        (out, err) = runCommand(command)
        if out:
            txt_version = out[0].strip('\n ')

    file_name = os.path.join(product_dir, 'profiles/default/metadata.xml')
    if os.path.exists(file_name):
        lines = []
        read_zopeconffile(file_name, lines)
        found = False
        for line in lines:
            line = line.strip('\n\t ')
            if line.startswith('<version>'):
                line = line[9:].replace('</version>','')
                xml_temp = line.strip('\n\t ')
                if found and xml_version != xml_temp:
                    error("Already found xml version ('%s' <> new '%s') in '%s'"%(xml_version, xml_temp, file_name))
                xml_version = xml_temp
                found = True

    if txt_version and xml_version:
        if txt_version != xml_version:
            return "%s | %s"%(xml_version, txt_version)
        else:
            return txt_version
    elif xml_version:
        return xml_version
    elif txt_version:
        return txt_version
    return None

#------------------------------------------------------------------------------

def getRevision(lines):
    """ get the revision number from the svn info output """
    for line in lines:
        rev_nb = line.strip('\n ')
        #works on all2all server
        if re.compile(r'^R.vision ?: (\d+)$').match(rev_nb):
            rev_nb = re.compile(r'^R.vision ?: (\d+)$').match(rev_nb).group(1)
#            verbose("Local revision = %s"%rev_nb)
            return rev_nb
        #works locally
        elif re.compile(r'^Révision ?: (\d+)$').match(rev_nb):
            rev_nb = re.compile(r'^Révision ?: (\d+)$').match(rev_nb).group(1)
#            verbose("Local revision = %s"%rev_nb)
            return rev_nb
    error("Revision not matched")
    return None

#------------------------------------------------------------------------------

def getRepositoryVersion(url, product):
    """ get the content of the repository version.txt file and revision number """
    global temp_added
    rep_version = rep_rev = 0
    if not os.path.exists(tempdir):
        try:
            os.mkdir(tempdir)
            temp_added = True
        except Exception, errmsg:
            error("cannot create temp dir '%s'"%tempdir)
            return(None, None)
    os.chdir(tempdir)
    command = 'svn co %s %s'%(url, product)
    (cmd_out, cmd_err) = runCommand(command)
    if cmd_err:
        error("error running command %s : %s" % (command, ''.join(cmd_err)))
        return(rep_version, rep_rev)

    product_dir = os.path.join(tempdir, product)
    os.chdir(product_dir)
    rep_version = getLocalVersion(product_dir)
#    verbose("rep version=%s"%rep_version)

    svn_cmd = 'svn info'
    (svn_out, svn_err) = runCommand(svn_cmd)
    if svn_err:
        error("error running command %s : %s" % (svn_cmd, ''.join(svn_err)))
        return(rep_version, rep_rev)
    elif svn_out:
        rep_rev = getRevision(svn_out)
    else:
        error('No output for command %s'%svn_cmd)

    shutil.rmtree(os.path.join(tempdir, product))
    return(rep_version, rep_rev)

#------------------------------------------------------------------------------

def read_zopeconffile(zodbfilename, lines):
    """ read the zope conf filename and include subfile """
    try:
        zfile = open( zodbfilename, 'r')
    except IOError:
        error("! Cannot open %s file" % zodbfilename)
        return
    for line in zfile.readlines():
        line = line.strip('\n\t ')
        if line.startswith('%include'):
            otherfilename = line.split()[1]
            read_zopeconffile(otherfilename, lines)
            continue
        lines.append(line)
    zfile.close()

#------------------------------------------------------------------------------

def treat_zopeconflines(zodbfilename, fspath, inst_id):
    """
        read zope configuration lines to get informations
    """
    lines = []
    read_zopeconffile(zodbfilename, lines)

    httpflag = False
    mp_name = mp_path = mp_fs = mp_fspath = None
    mp_size = 0
    for line in lines:
        line = line.strip()
        if line.startswith('<http-server>'):
            httpflag = True
            continue
        if line.startswith('<zodb_db '):
            #<zodb_db main>
            if mp_name:
                error("\tnext db found while end tag not found: previous dbname '%s', current line '%s'"%(mp_name, line))
            mp_name = line.split()[1]
            mp_name = mp_name.strip('> ')
            if mp_name == 'temporary':
                mp_name = None
            continue
        if mp_name and line.startswith('</zodb_db>'):
            insertInTable('mountpoints', "instance_id, name, path, fs, size, fspath", "%s, '%s', '%s', '%s', %s, '%s'"
                %(inst_id, mp_name, mp_path, mp_fs, mp_size, mp_fspath))
            mp_name = mp_path = mp_fs = mp_fspath = None
            mp_size = 0
            continue
        if mp_name and line.startswith('path '):
            #path $INSTANCE/var/Data.fs
            mp_fs = os.path.basename(line.split()[1])
            if not mp_fs.endswith('.fs'):
                error("Error getting fs name in '%s'"%line)
            mp_fspath = os.path.join(fspath, mp_fs)
            if os.path.exists(mp_fspath):
                mp_size = int(os.path.getsize(mp_fspath)/1048576)
            else:
                error("Db file '%s' doesn't exist"%mp_fspath)
                mp_fspath = ''
            continue
        if mp_name and line.startswith('mount-point '):
            #mount-point /
            mp_path = line.split()[1]
            if not mp_path.startswith('/'):
                error("Error getting path name in '%s'"%line)
            continue
        if httpflag and line.startswith('address'):
            port = line.split()[1]
            updateTable('instances', "port=%s"%(port), "id = %s"%inst_id)
    return port

#------------------------------------------------------------------------------

def read_zopectlfile(zopectlfilename, inst_id):
    """ read the zopectl file to find the zope path and zope version"""
    try:
        zfile = open( zopectlfilename, 'r')
    except IOError:
        error("! Cannot open %s file" % zopectlfilename)
        return
    for line in zfile.readlines():
        line = line.strip('\n\t ')
        if line.startswith('ZOPE_HOME'):
            zopepath = line.split('=')[1]
            zopepath = zopepath.strip('"\' ')
            if not updateTable('instances', "zope_path='%s'"%(zopepath), "id = %s"%inst_id):
                sys.exit(1)
            zope_version = getLocalVersion(os.path.join(zopepath, 'lib/python/Zope2'))
            if zope_version:
                updateTable('instances', "zope_version='%s'"%(zope_version), "id = %s"%inst_id)

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

def getProductId(product):
    row = selectOneInTable('products', 'id', "product = '%s'"%product)
    if row:
        return row[0]
    return 0

#------------------------------------------------------------------------------

def getServerId():
    row = selectOneInTable('servers', 'id', "server = '%s'"%socket.gethostname())
    if row:
        return row[0]
    return 0

#------------------------------------------------------------------------------

def getInstanceId(instance):
    row = selectOneInTable('instances', 'id', "instance = '%s'"%instance)
    if row:
        return row[0]
    return 0

#------------------------------------------------------------------------------

def getInstancesProductsId(inst_id, product_id):
    row = selectOneInTable('instances_products', 'id', "instance_id = %s and product_id = %s"%(inst_id, product_id))
    if row:
        return row[0]
    return 0

#------------------------------------------------------------------------------

def insertInstancesProducts(instance, product, local_version, rep_version, local_rev, rep_rev, diff_flag, rep_url, diff_out, diff_count):
    inst_id = getInstanceId(instance)
    product_id = getProductId(product)
    if not product_id:
        if not insertInTable('products', "product", "'%s'"%(product)):
            sys.exit(1)
        product_id = getProductId(product)

    #testing if a row already exists for this instance and this product
    inst_prod_id = getInstancesProductsId(inst_id, product_id)
    if inst_prod_id:
        error("row already exists for instance = %s and product = %s"%(instance, product))
        deleteTable('instances_products', "id = %s"%inst_prod_id)

    #inserting new row
    if not insertInTable('instances_products', "instance_id, product_id", "%s, %s"%(inst_id, product_id)):
        sys.exit(1)
    inst_prod_id = getInstancesProductsId(inst_id, product_id)

    #updating other columns if they are not None
    if local_version and not updateTable('instances_products', "local_version='%s'"%(local_version), "id = %s"%inst_prod_id):
        sys.exit(1)
    if rep_version and not updateTable('instances_products', "repository_version='%s'"%(rep_version), "id = %s"%inst_prod_id):
        sys.exit(1)
    if local_rev and not updateTable('instances_products', "local_revision=%s"%(local_rev), "id = %s"%inst_prod_id):
        sys.exit(1)
    if rep_rev and not updateTable('instances_products', "repository_revision='%s'"%(rep_rev), "id = %s"%inst_prod_id):
        sys.exit(1)
    if diff_flag and not updateTable('instances_products', "svn_diff='%s'"%(diff_flag), "id = %s"%inst_prod_id):
        sys.exit(1)
    if diff_count and not updateTable('instances_products', "svn_diff_lines='%s'"%(diff_count), "id = %s"%inst_prod_id):
        sys.exit(1)
    if rep_url and not updateTable('instances_products', "repository_address='%s'"%(rep_url), "id = %s"%inst_prod_id):
        sys.exit(1)

#    tab_file.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n"%(product, local_version, rep_version, local_rev, rep_rev, diff_flag, diff_count, rep_url))

#    if not diff_file:
#        filename = os.path.join(pdir, '..', 'Extensions', diff_filename)
#        try:
#            diff_file = open(filename, 'w')
#        except IOError:
#            error("Cannot create %s file" % filename)
#            sys.exit(1)
#    if diff_count:
#        diff_file.write('==> %s\n'%product)
#        diff_file.write('='*80)
#        diff_file.write('\n'+ ''.join(diff_out) + '\n\n')

#------------------------------------------------------------------------------

try:
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-i", "--infos", dest="infos",
                  default=None,
                  help="infos about instance formatted like: "
                       "\"instance_path;transactions_days_number;admin_user;admin_password\"")
    (options, args) = parser.parse_args()
    if options.infos.startswith('#'):
        sys.exit(0)
    instdir, days, user, pwd = options.infos.split(';')
except ValueError:
    error("Problem in parameters")
    parser.print_help()
    sys.exit(1)

if __name__ == '__main__':
    verbose("Begin of %s"%sys.argv[0])
#    sys.exit(0)
    main()
    verbose("End of %s"%sys.argv[0])
