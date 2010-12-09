#####!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Script to analyse apache conf files
# Stéphan Geulette <stephan.geulette@uvcw.be>, UVCW
#

import sys, os, string, re, shutil, socket
from datetime import datetime, timedelta
from postgres_utilities import *

def verbose(*messages):
    print '>>', ' '.join(messages)
def error(*messages):
    print >>sys.stderr, '!!', (' '.join(messages))
def trace(*messages):
    if not TRACE: return
    print 'TRACE:', ' '.join(messages)
TRACE = False

apaches = (
#    {'name':'apache2','type':'d', 'path':'./sites-available'},
#    {'name':'apacheocsp','type':'f', 'path':'httpd.conf'},
    {'name':'apache2','type':'d', 'path':'/etc/apache2/sites-enabled'},
    {'name':'apacheocsp','type':'f', 'path':'/srv/apache/apache2OCSP/conf/httpd.conf'},
)

pat_virtualhost     = re.compile(r"^<virtualhost +([\d\.:]+) *>",re.I)
pat_virtualhost_end = re.compile(r"^</virtualhost",re.I)
pat_servername      = re.compile(r'^servername +(.+)', re.I)
pat_serveralias     = re.compile(r'^serveralias +(.+)', re.I)
pat_log             = re.compile(r'^customlog +(\S+) *(combined)?', re.I)
pat_serverroot      = re.compile(r'^serverroot +(?:\'|\")?(.+)(\'|\")', re.I)
pat_rw_begin        = re.compile(r'^rewriterule +', re.I)
pat_rw_other        = re.compile(r'^rewriterule +\^?/(stats|awstats|svn/|trac(/|\$))', re.I)
pat_rw_map_mini     = re.compile(r'^rewritemap map-mini +(.+)', re.I)
pat_rw_zope         = re.compile(r'^rewriterule +\^?/([\w-]*)(?:\(\.\*\)?) +http://localhost:(\d+)/VirtualHostBase/(https?)/([\w\-\.]+):(\d+)/([\w\-/]+)/VirtualHostRoot/', re.I)
pat_redirect_begin  = re.compile(r'^redirect +', re.I)
pat_redirect        = re.compile(r'^redirect +(\d+) +([\w\-/]+) +([\w\-/:\.]+)', re.I)
#Redirect 301 / https://andenne.lescommunes.be
#RewriteRule ^/floreffe(.*) http://localhost:9009/VirtualHostBase/http/www.communesplone.be:80/floreffe/floreffe/VirtualHostRoot/_vh_floreffe/$1 [P,L]
#RewriteRule ^/(.*) http://localhost:9009/VirtualHostBase/https/andenne.lescommunes.be:443/andenne/andenne/VirtualHostRoot/$1 [L,P]
#RewriteRule ^/stats

serverroot = log = None
now = datetime(1973,02,12).now()

###############################################################################

def main():
    verbose("Begin of %s"%sys.argv[0])
    global serverroot, log

    row = selectOneInTable('apaches', 'min(creationdate)')
    if row[0] and (now - row[0]) > timedelta(hours=3):
#    if row[0] and (now - row[0]) > timedelta(minutes=8):
#    if True:
        deleteTable('apaches')
        deleteTable('virtualhosts')
        deleteTable('rewrites')
    row = selectOneInTable('servers', 'min(creationdate)')
    if not row[0] or (now - row[0]) > timedelta(hours=5):   
#    if True: 
        deleteTable('servers')    

    hostname = socket.gethostname()
    row = selectOneInTable('servers', '*', "server = '%s'"%hostname)
    if not row and not insertInTable('servers', "server, ip_address,creationdate", "'%s', '%s', '%s'"
                %(hostname, socket.gethostbyname(hostname),now)):    
        sys.exit(1)
    server_id = getServerId(hostname)

    for apache_dic in apaches:
        serverroot = log = None
        if apache_dic['type'] == 'f':
            analyze_conf(apache_dic['path'], apache_dic['name'], server_id)
        elif apache_dic['type'] == 'd':
            if not os.path.isdir(apache_dic['path']):
                error("directory '%s' doesn't exist"%apache_dic['path'])
                continue
            fileslist = os.listdir(apache_dic['path'])
            fileslist.sort()
            for filename in fileslist:
                filepath = os.path.join(apache_dic['path'], filename)
                if not os.path.isdir(filepath):             
                    analyze_conf(filepath, apache_dic['name'], server_id)

    verbose("End of %s"%sys.argv[0])

#------------------------------------------------------------------------------

def analyze_conf(conf_file, apache_name, server_id):
    """ read an apache conf file """
    global serverroot, log
    if not os.path.isfile(conf_file):
        error("Filename passed is not a file : '%s'"%conf_file)
        return
#    if not conf_file.endswith('all.communesplone.be.pilot'):
#        return
    verbose("Working on '%s'"%conf_file)
    if not insertInTable('apaches', "name, conf_file, creationdate, server_id", "'%s', '%s', '%s', %s"%(apache_name, conf_file, now, server_id)):
        sys.exit(1)
    apache_id = 0
    row = selectOneInTable('apaches', 'id', "conf_file = '%s' and server_id = %s"%(conf_file, server_id))
    if row:
        apache_id = row[0]
    try:
        cfile = open( conf_file, 'r')
    except IOError:
        error("Cannot open %s file" % conf_file)
        return
    vhost = servername = minisite = log_vh = redirect_code = redirect_from = redirect_to = servernameip = protocol = vh_ip = ''
    serveralias = []
    rewrites = []    
    maps_mini_dico = {}
    lnb = 0    
    for line in cfile.readlines():
        lnb += 1
        line = line.strip(' \t\n')
        if not line or line[0] == '#':
            continue

        #<VirtualHost 62.58.108.100:80>
        res = pat_virtualhost.match(line)
        if res:
            vhost = res.group(1)
            if vhost.find(':') > 0:
                (vh_ip, port) = vhost.split(':')
                protocol = (port == '80' and 'http' or (port == '443' and 'https' or '')) 
            del(serveralias[:]) #we must clear server alias because we have a new VirtualHost definition
            continue

        #ServerName www.communesplone.be
        res = pat_servername.match(line)
        if res:
            servername = res.group(1)
            servernameip = getServernameIP(servername)
            trace("servername='%s'"%servername)
            continue
        
        #ServerAlias
        res = pat_serveralias.match(line)
        if res:
            serveralias.append(res.group(1))
            trace("serveralias='%s'"%res.group(1))
            continue        

        #RewriteMap map-mini srv/minisites.d/filename.conf
        res = pat_rw_map_mini.match(line) 
        if res:            
            minisite = res.group(1)
            continue

        #ServerRoot "/usr/local/apache2OCSP"
        res = pat_serverroot.match(line)
        if res:
            if serverroot:
                error("Already a server root for this apache '%s' <=> '%s'"%(serverroot,res.group(1)))
            else:
                serverroot = res.group(1)
            continue

        #CustomLog /var/apache_logs/communesplone_access.log combined
        res = pat_log.match(line)
        if res:
            if vhost:
                log_vh = res.group(1)
            elif log:
                error("Already a server log for this apache '%s' <=> '%s'"%(log,res.group(1)))
            else:
                log = res.group(1)

        #RewriteRule ^/floreffe(.*) http://localhost:9009/VirtualHostBase/http/www.communesplone.be:80/floreffe/floreffe/VirtualHostRoot/_vh_floreffe/$1 [P,L]
        #RewriteRule ^/(.*) http://localhost:9009/VirtualHostBase/https/andenne.lescommunes.be:443/andenne/andenne/VirtualHostRoot/$1 [L,P]
        #pat_rw_begin        = re.compile(r'^rewriterule +', re.I)
        #pat_rw_other        = re.compile(r'^rewriterule +\^?/(stats|awstats|svn/|trac(/|\$))', re.I)
        #pat_rw_zope         = re.compile(r'^rewriterule +\^?/([\w-]*)(?:\(\.\*\)?) +http://localhost:(\d+)/VirtualHostBase/(https?)/([\w\-\.]+):(\d+)/([\w\-/]+)/VirtualHostRoot/', re.I)
        if pat_rw_begin.match(line):            
            res = pat_rw_other.match(line)
            if res:
                continue   
            maps_mini_dico.clear() #we must clear dico because we can have some virtualhost definition in one file
            maps_mini_dico[servername] = '' #initialize main virtualhost definition
            for sa in serveralias:
                if sa.startswith('*.') or servername.find(sa)>=0:
                    continue
                maps_mini_dico[sa] = ''            
            if minisite:
                try:
                    minifile = open(minisite, 'r')
                    for miniline in minifile.readlines():
                        miniline = miniline.strip(' \n')
                        if miniline and not miniline.startswith('#'):
                            try:
                                domain,path = miniline.split(' ')                            
                                if maps_mini_dico.has_key(domain) and maps_mini_dico[domain]:
                                    error("this key for minisite already exist and have a value")
                                else:
                                    maps_mini_dico[domain] = '/'+path
                            except ValueError: 
                                error("Bad formatting in minisite line %"%miniline)
                except IOError:                
                    error("Cannot open %s file" % minisite)
            map_mini_keys = maps_mini_dico.keys()
            for map_mini_key in map_mini_keys:   
                adaptedline = line.replace('/${map-mini:%{SERVER_NAME}}',maps_mini_dico[map_mini_key])
                adaptedline = adaptedline.replace('%{SERVER_NAME}',map_mini_key)
                res = pat_rw_zope.match(adaptedline)
                if res:
                    rewrites.append((res.group(1), res.group(2), res.group(3), res.group(4), res.group(5), res.group(6)))
                    trace("folder='%s', zopeport='%s', protocol='%s', domain='%s', port='%s', path='%s'"%(res.group(1), res.group(2), res.group(3), res.group(4), res.group(5), res.group(6)))
                else:
                    error("Matching missed in RewriteRule line %d:'%s'"%(lnb,line))
                if line.find('%{SERVER_NAME}')<0:
                    break

        #Redirect 301 / https://andenne.lescommunes.be
        #pat_redirect_begin  = re.compile(r'^redirect +', re.I)
        #pat_redirect        = re.compile(r'^redirect +(\d+) +([\w\-/]+) +([\w\-/:\.]+)', re.I)
        if pat_redirect_begin.match(line):
            res = pat_redirect.match(line)
            if res:
#                print "code=%s, from='%s', to='%s'"%(res.group(1), res.group(2), res.group(3))
                redirect_code = res.group(1)
                redirect_from = res.group(2)
                redirect_to = res.group(3)
            else:
                error("Matching missed in Redirect line %d:'%s'"%(lnb,line))


        #</VirtualHost>
        if pat_virtualhost_end.match(line):
            if not vhost:
                error("Found the end of a virtualhost while begin was not found, %d:'%s'"%(lnb,line))
                vhost = servername = log_vh = redirect_code = redirect_url = protocol = vh_ip = ''
                continue
            #storing virtualhost
            if not servername and not log and log_vh:
                log = log_vh
            tmplog = log_vh
            if not log_vh:
                tmplog = 'default: '+log
            tmpred = ''
            if redirect_code:
                tmpred = redirect_from + ' -> ' + redirect_to
            if not insertInTable('virtualhosts', "apache_id, virtualhost, servername, logfile, redirect, real_ip, protocol, virtualhost_ip", "%s, '%s', '%s', '%s', '%s', '%s', '%s', '%s'"%(apache_id, vhost, servername, tmplog, tmpred, servernameip, protocol, vh_ip)):
                sys.exit(1)
#            print "vhost='%s', server='%s', root='%s', log='%s', log_vh='%s'"%(vhost, servername, serverroot, log, log_vh)
            row = selectOneInTable('virtualhosts', 'max(id)', "apache_id = %s and servername = '%s'"%(apache_id, servername))
            vh_id = row[0]
            #storing rewrites
            for rw in rewrites:
                tmpdom = rw[3]
                if rw[0]:
                    tmpdom += '/'+rw[0]
                if not insertInTable('rewrites', "virtualhost_id, port, protocol, domain, inst_path", "%s, %s, '%s', '%s', '%s'"%(vh_id, rw[1], rw[2], tmpdom, '/'+rw[5])):
                    sys.exit(1)

            vhost = servername = log_vh = redirect_code = redirect_from = redirect_to = servernameip = protocol = vh_ip = ''
            rewrites = []

    cfile.close()

#------------------------------------------------------------------------------

def getServerId(hostname):
    row = selectOneInTable('servers', 'id', "server = '%s'"%hostname)
    if row:
        return row[0]
    return 0

#------------------------------------------------------------------------------

def getServernameIP(servername):
    diff_cmd = 'ping -c 1 -q %s'%servername
    (diff_out, diff_err) = runCommand(diff_cmd)
    pat_ping = re.compile(r'^PING +\S+ +\(([\d\.]+)\).+', re.I)
    ip = ''
    if diff_err:
        error("error running command %s : %s" % (diff_cmd, ''.join(diff_err)))
    elif diff_out:
        for line in diff_out:
            line = line.strip()
            res = pat_ping.match(line)
            if res:
                ip = res.group(1)
                break
    if not ip:
        error("server:%s without IP ?"%(servername))
    return ip

#------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
