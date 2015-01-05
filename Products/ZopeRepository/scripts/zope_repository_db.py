#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Script to create and update a repository on zope instances
# Stéphan Geulette <stephan.geulette@uvcw.be>, UVCW
#

import sys, os, commands, string, re, shutil
import urllib
from datetime import datetime, timedelta
import socket
from postgres_utilities import *
import ConfigParser as cfgparser
from setuptools.command.easy_install import *

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
#dsn="host=localhost port=5432 dbname=zoperepos user=zoperepos password=zopeREP1"
#dsn is now in postgres_utilities
ext_method = 'zope_repository_infos'
ext_filename = 'zope_infos.py'
function = 'walkInZope'
TRACE = False
DOSTATWORK=True

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

    if os.path.exists(os.path.join(instdir, 'parts/instance')):
        instance_name = 'instance'
    elif os.path.exists(os.path.join(instdir, 'parts/instance1')):
        instance_name = 'instance1'
    else:
        error("! instance name in '%s' not found" % instdir)
        sys.exit(1)

    if buildout_inst_type:
        zodbfilename = os.path.join(instdir, 'parts/%s/etc/zope.conf' % instance_name)
        zopectlfilename = os.path.join(instdir, 'parts/%s/bin/zopectl' % instance_name)
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
    if row[0] and (now - row[0]) > timedelta(hours=20):
#    if row[0] and (now - row[0]) > timedelta(minutes=8):
#    if True:
        deleteTable('instances')
        deleteTable('products')
        deleteTable('instances_products')
        deleteTable('plonesites')
        deleteTable('plonesites_products')
        deleteTable('mountpoints')
        deleteTable('fsfiles')
    row = selectOneInTable('servers', 'min(creationdate)')
    if not row[0] or (now - row[0]) > timedelta(hours=20):        
        deleteTable('servers') 
    row = selectOneInTable('lastProduct_version', 'min(creationdate)')
    if not row[0] or (now - row[0]) > timedelta(hours=68):        
        deleteTable('lastProduct_version')    

    #hostname = '127.0.0.1' # to test if it work with another hostname
    #Creation or update of the server information
    row = selectOneInTable('servers', '*', "server = '%s'"%hostname)
    if not row and not insertInTable('servers', "server, ip_address,creationdate", "'%s', '%s', '%s'"
                %(hostname, socket.gethostbyname(hostname),now)):
        sys.exit(1)
    server_id = getServerId(hostname)    
    (is_svn, rep_url, local_rev) = svnInformation(instdir)    
    rep_rev = ''
    svn_diff = ''    
    if is_svn:
        (rep_version, rep_rev) = getRepositoryVersion(rep_url, "temp")
        #dir was changed in getRepositoryVersion()
        os.chdir(instdir)
        if local_rev != rep_rev or not local_rev or not rep_rev:
            local_rep = rep_url + '@' + local_rev.strip(' ')
            server_rep = rep_url + '@HEAD'
            diff_cmd = 'svn diff ' + local_rep + ' ' + server_rep
            verbose(str(diff_cmd))
            (diff_out, diff_err) = runCommand(diff_cmd)
            if diff_err:
                error("error running command %s : %s" % (diff_cmd, ''.join(diff_err)))
            elif diff_out:
                svn_diff = 'Yes'
                diff_lines = diff_out
                diff_count = len(diff_out)
            else:
                svn_diff = 'No'    
        elif local_rev == rep_rev:
            svn_diff = 'No' 
    #Creation or update of the instance information
    inst_id = getInstanceId(instance, server_id)
    if inst_id:
        if not updateTable('instances', "creationdate='%s'"%(now), "id = %s"%inst_id):
            sys.exit(1)
        if not updateTable('instances', "type='%s'"%(inst_type), "id = %s"%inst_id):
            sys.exit(1)
        if not updateTable('instances', "repository_address='%s'"%(rep_url), "id = %s"%inst_id):
            sys.exit(1)
        deleteTable('instances_products', "instance_id = %s"%inst_id)
        deleteTable('plonesites', "instance_id = %s"%inst_id)
        deleteTable('mountpoints', "instance_id = %s"%inst_id)
    elif not insertInTable('instances', "instance, creationdate, type, server_id, repository_address, svn_diff, local_revision, repository_revision", "'%s', '%s', '%s', %s, '%s', '%s', '%s', '%s'"
                %(instance, now, inst_type, server_id, rep_url, svn_diff,local_rev,rep_rev)):
        sys.exit(1)

    inst_id = getInstanceId(instance, server_id)

    # Getting some informations in zopectl file (zope path, zope version)
    read_zopectlfile(zopectlfilename, inst_id)

    # Getting some informations in zope.conf file (port, mount points)
    port = treat_zopeconflines(zodbfilename, fspath, inst_id)

    # Getting products and eggs in a list
    eggsFind = []
    readProductsDir(productsdir, pfolders, eggsFind)

#    input('Press a key to continue')
#    return
    verbose("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"
        %('Product', 'Local version', 'Rep version', 'Local rev', 'Rep rev', 'Diff flag', 'Rep url', 'Diff lines', 'Diff count'))

    fkeys = pfolders.keys()
   
    fkeys.sort()    
    
    mostVersionDic = readLastProductVersion()
 
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
        (is_svn, rep_url, local_rev) = svnInformation(pfolders[product])

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
        else:
            #check if it's an egg and get informations           
            #egg_cmd = os.path.join(instdir, 'bin/') + "easy_install --dry-run " + product  
            if not mostVersionDic.has_key(product):   
                egg_cmd = os.path.join(instdir, 'bin/') + "easy_install -f http://download.zope.org/ppix/,http://download.zope.org/distribution/,http://effbot.org/downloads,http://dist.plone.org --dry-run " + product 
                try:
                    (egg_out, egg_err) = runCommand(egg_cmd)
                    if egg_out:
                        for eggout in egg_out:
                            if (eggout.find("Best match: " + product) != -1) and (eggout != 'Best match: None'):
                                rep_version = eggout.strip(" ").split(" ")[3]
                                break
                    mostVersionDic[product] = rep_version
                    row = selectOneInTable('lastProduct_version', '*', "product = '%s'"%product)
                    if not row and not insertInTable('lastProduct_version', "product, creationdate, repository_revision", "'%s', '%s', '%s'"%(product, now, rep_version)):
                        sys.exit(1)                      
                except Exception, msg:
                    error("Cannot run easy_install command for %s (%s)"%(product, msg)) 
            else:
                rep_version = mostVersionDic[product]
                
        #check if it's an egg 
        is_egg = isAnEgg(product,eggsFind)
        trace("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"
            %(product, local_version, rep_version, local_rev, rep_rev, diff_flag, rep_url, diff_lines, diff_count,is_egg))
        diff_lines_to_print = diff_lines
        if diff_lines_to_print:
            diff_lines_to_print = 'too long'
        verbose("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s"
            %(product, local_version, rep_version, local_rev, rep_rev, diff_flag, rep_url, diff_lines_to_print, diff_count,is_egg))
        insertInstancesProducts(server_id, instance, product, local_version, rep_version, local_rev, rep_rev, diff_flag, rep_url, diff_lines, diff_count, is_egg)
                
    product_id = getProductId('Products.CMFPlone')
    if product_id:
        row = selectOneInTable('instances_products', 'local_version', "instance_id = %s and product_id = %s"%(inst_id, product_id))        
        if row:
            updateTable('instances', "plone_version='%s'"%(row[0]), "id = %s"%inst_id)

    if temp_added:
        shutil.rmtree(tempdir) 
        
    # Getting all fs file   
    verbose('threat fsfiles in', fspath)
    folderLst = os.listdir(fspath) 
    for fileInFolder in folderLst:
        completeFsFileName = fspath + fileInFolder
        if not os.path.isfile(completeFsFileName):
            continue
        fsSize = os.path.getsize(completeFsFileName)/1048576
        (fileName, fileExt) = os.path.splitext(fileInFolder)
        if fileExt == '.fs':            
            if not getFsFilesId(inst_id,fileInFolder):
                #inserting new row
                if not insertInTable('fsfiles', "instance_id, fs, path, size", "%s, '%s', '%s', %s"%(inst_id, fileInFolder, completeFsFileName, fsSize)):
                    sys.exit(1)   
                    
    #awstats construct
    if DOSTATWORK and instance.find('test')<0 and instance.find('Test')<0 and instance.find('transmo')<0 and instance.find('transmo')<0:
        logfilepath = os.path.join(instdir, 'var/awstats')
        #get all log file for this instance
        rows = getAllLogFile(inst_id)
        logfiles = ""
        for row in rows:
            myRedirectLog = os.path.join('/srv/apache2-logs',row[0].split('/')[-1])     
            if os.path.isfile(myRedirectLog) and logfiles.find(myRedirectLog)<0:
                logfiles = logfiles + myRedirectLog + ' '    
        #construct conf file for awstats and laungh script  
        filename = os.path.join(logfilepath, 'awstats.' + instance + '.conf')  
        try:
            if not os.path.isdir(logfilepath):
                os.makedirs(logfilepath, mode=0777) 
            if not os.path.isfile(filename):
                file(filename, 'wt')                
            confFile = open(filename, 'w') 
            confFile.write('LogFile="/usr/share/doc/awstats/examples/logresolvemerge.pl '+ logfiles+'|"\n')
            confFile.write('LogFormat=1\n')
            confFile.write('SiteDomain="'+instance+'"\n')
            confFile.write('HostAliases="REGEX[.*]"\n')
            confFile.write('DirData="'+logfilepath+'"\n')
            confFile.write('DirIcons="/awstats/icon"\n')
            #confFile.write('LoadPlugin="geoip GEOIP_STANDARD /usr/share/awstats/lib/GeoIP.dat"\n')
            confFile.close();
            command = "%s -config=%s -configdir=%s update"%('/usr/lib/cgi-bin/awstats.pl', instance,logfilepath)
            verbose("\t>> Running '%s'"%command)
            (cmd_out, cmd_err) = runCommand(command)
            if cmd_err:
                error("error running command %s : %s" % (command, ''.join(cmd_err)))
            if cmd_out:
                verbose("\t>>OUTPUT: %s" % (''.join(cmd_out))) 
            awstats_path = 'http://' + hostname + '-stats.communesplone.be/stats/awstats.pl?config=' + instance + '&configdir=' + logfilepath
            if not updateTable('instances', "awstats_path='%s'"%(awstats_path), "id = %s"%inst_id):
                sys.exit(1)
        except Exception, msg:
            error("Erreur lors de l'ouverture du fichier awstats ! (%s)"%msg)

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

def readProductsDir(pdir, dic, eggsFind):
    """ Read the products dir and save the folder names in a dic """
    if not os.path.exists(pdir):
        error("Dir products '%s' doesn't exist"%pdir)
        return 
    for (dirname, path) in getSubdirs(pdir):
        dirname = "Products." + dirname
        dic[dirname] = path
    #now, we must add all other eggs (not begining by Products.xxx)    
    config = cfgparser.ConfigParser()
    configFile = instdir+"/buildout.cfg"
    config.read(configFile)
    has_section = config.has_section("instance") # return True if section exist (Caution is mother of safety)
    if has_section:
        has_option = config.has_option("instance", "eggs") # return True if option exist
        if has_option:
            eggs = config.get("instance", "eggs").split("\n")
            for egg in eggs:
                if egg and egg[0] != "$":
                    eggsFind.append(egg)
                    if egg[0:8] == "Products": #egg in Products.xxx form already threated
                        continue
                    egg = egg.strip(" ").split(" ")[0]
                    path = os.path.join(instdir, 'parts/omelette', egg.replace(".","/"))
                    if os.path.exists(path):
                        dic[egg] = path  #add in dictionnaries this egg    
    trace(str(dic))

#------------------------------------------------------------------------------

def isAnEgg(product,eggs):
    for egg in eggs:
        if egg.find(product) != -1:
            return "Yes"
    return "No"

#------------------------------------------------------------------------------

def readLastProductVersion():     
    mostVersionDic={}
    rows = selectWithSQLRequest("select product,repository_revision from lastProduct_version")   
    for row in rows:
        mostVersionDic[row[0]] = row[1]
    return mostVersionDic

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

def svnInformation(dirpath):
    """ get svn information on a directory """
    os.chdir(dirpath)
    #Testing if product is svn linked
    is_svn = True
    local_rev = None
    rep_url = None
    svn_cmd = 'svn info'
    try:
        (svn_out, svn_err) = runCommand(svn_cmd)
        if svn_err:
            if svn_err[0].startswith("svn: '.' "):
                is_svn = False
            else:
                error("error running command %s : %s" % (svn_cmd, ''.join(svn_err)))
        elif svn_out:
            #trace('output=%s'%"".join(svn_out))
            #Getting svn repository url
            rep_url = svn_out[1].strip('\n ')
            if rep_url.startswith('URL'):
                rep_url = rep_url[3:].strip(' :') 
                #rep_url = rep_url[7:]
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
    except:
        error('Anormal end of svnInformation (%s)'%dirpath)
    return(is_svn, rep_url, local_rev)

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
    else:
        file_name = os.path.join(product_dir, 'VERSION.txt')
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
            return rev_nb
        #works locally
        elif re.compile(r'^Révision ?: (\d+)$').match(rev_nb):
            rev_nb = re.compile(r'^Révision ?: (\d+)$').match(rev_nb).group(1)
            return rev_nb
        else:
            if rev_nb.find('Révision') != -1:
                return rev_nb[rev_nb.find('Révision') + len('Révision')+3:]
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
    try:
        (cmd_out, cmd_err) = runCommand(command)
        if cmd_err:
            error("error running command %s : %s" % (command, ''.join(cmd_err)))
            return(rep_version, rep_rev)
    except:
        error("error running command %s in getRepositoryVersion" %command)
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

def getProductId(product):
    row = selectOneInTable('products', 'id', "product = '%s'"%product)
    if row:
        return row[0]
    return 0

#------------------------------------------------------------------------------

def getServerId(hostname):
    row = selectOneInTable('servers', 'id', "server = '%s'"%hostname)
    if row:
        return row[0]
    return 0

#------------------------------------------------------------------------------

def getInstanceId(instance, server_id):
    row = selectOneInTable('instances', 'id', "instance = '%s' and server_id = %d"%(instance, server_id))
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

def getFsFilesId(inst_id, fs):
    row = selectOneInTable('fsfiles', 'id', "instance_id = %s and fs = '%s'"%(inst_id, fs))
    if row:
        return row[0]
    return 0

#------------------------------------------------------------------------------

def insertInstancesProducts(server_id, instance, product, local_version, rep_version, local_rev, rep_rev, diff_flag, rep_url, diff_out, diff_count, is_egg):
    inst_id = getInstanceId(instance, server_id)
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
    if is_egg and not updateTable('instances_products', "is_egg='%s'"%(is_egg), "id = %s"%inst_prod_id):
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


def getAllLogFile(inst_id): 
    sql = "select distinct logfile from virtualhosts vir, rewrites rew, apaches ap, servers srv, instances inst \
    where vir.id = rew.virtualhost_id and \
    vir.apache_id = ap.id and \
    ap.server_id = srv.id and \
    srv.id = inst.server_id and \
    inst.port = rew.port and inst.id = " + str(inst_id)
    return selectWithSQLRequest(sql)

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
