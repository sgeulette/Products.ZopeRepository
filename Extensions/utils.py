#utilities
# -*- coding: utf-8 -*-
# This script must be called in a zope instance

__author__ = """André NUYENS <andre.nuyens@uvcw.be>"""
__docformat__ = 'plaintext'

import os
import logging

from Products.ZopeRepository.config import FILES_FOLDER

###############################################################################

def check_role(self, role='Manager', context=None):
    from Products.CMFCore.utils import getToolByName
    pms = getToolByName(self, 'portal_membership')
    return pms.getAuthenticatedMember().has_role(role, context)

###############################################################################

def check_zope_admin(self):
    from AccessControl.SecurityManagement import getSecurityManager    
    user = getSecurityManager().getUser()
    if user.has_role('Manager') and user.__module__ == 'Products.PluggableAuthService.PropertiedUser':
        return True
    return False
    
###############################################################################

def add_Gui_Files(self):
    """ external method called in the zope instance 
        use for copy all files from folder maintenanceFiles into current folder
    """    

    if not check_zope_admin(self):
        return 'add_Gui_Files run with a non admin user: we go out'  

    def install_pt(context, data, params, id):
        """Install a page template.
        """  
        #conversion list in string
        dataS = "".join(data)
        factory = context.manage_addProduct['PageTemplates']
        factory.manage_addPageTemplate(id, params.get('title','').strip() , dataS)
        out.append('"%s" : adding Page Template'%id)
        
    def install_py(context, data, params, id):
        """Install a Python script.
        """            
        dataS = "".join(data)
        factory = context.manage_addProduct['PythonScripts']
        factory.manage_addPythonScript(id)
        script = getattr(context, id)
        script.write(dataS)
        out.append('"%s" : adding Python script'%id)
        
    def install_DTML(context, data, params, id):
        """Install a DTML Document.
        """         
        dataS = "".join(data)
        factory = context.manage_addProduct['OFSP']
        factory.addDTMLDocument(id,params.get('title','').strip() ,file=dataS)
        out.append('"%s" : adding DTML Document'%id)
        
    def install_ZSQL(context, data, params, id):
        """Install a Z SQL Method.
        """    
        args = ""
        query = ""
        threatParams = True
        #transform <params>arg1,arg2,...,argN</params> in arg1,arg2,...,argN    
        for line in data:
            if threatParams:            
                if line.find('<params>')>=0:
                    line = line[8:]
                if line.find('</params>')>=0:
                    line = line[0:len(line)-10]
                    threatParams = False
                args = args + line
            else:
                query = query + line
        factory = context.manage_addProduct['ZSQLMethods']
        factory.manage_addZSQLMethod(id,params.get('title','').strip() ,'server_connection',args,query)
        out.append('"%s" : adding ZSQLMethods'%id)
        
    def install_ZPsycopg(context, data, params, id):
        """Install a Z Psycopg 2 Database connection.
        """      
        dataS = "".join(data)        
        factory = context.manage_addProduct['ZPsycopgDA'] 
        factory.manage_addZPsycopgConnection(id,params.get('title','').strip(),dataS.strip(),zdatetime=params.get('zdatetime','').strip(), encoding=params.get('encoding','').strip())   
        out.append('"%s" : adding Z Psycopg 2 Database connection'%id)        
    
    fileInFolder = ""     
    try:        
        out = []
        dicExt = {'.pt':install_pt, '.py':install_py, '.dtml':install_DTML, '.zsql':install_ZSQL, '.zpsy':install_ZPsycopg}     
        #get all file in list
        folderLst = os.listdir(FILES_FOLDER)         
        for fileInFolder in folderLst:        
            #open file and read info
            if os.path.isdir (fileInFolder):
                continue
            fileName = FILES_FOLDER + '/' + fileInFolder
            f = open(fileName,'r')
            t = f.readlines()
            f.close()
            #get name and extension (.pt, .ZQSL, .DTML, .py) >>> Meta-typ (Page Template, Z SQL Method, DTML Document, Script (Python))
            (fileName, fileExt) = os.path.splitext(fileInFolder)
            if not dicExt.has_key(fileExt):                
                out.append('"%s" : this extension is unknown'%fileExt)
                continue
            #get params {'title':'xxx',...} on first line
            params = eval(t[0])                  
            #get data (begin second line)
            data = list(t[1:])
            #create object
            if fileName not in self.objectIds():
                dicExt[fileExt](self, data, params, fileName)
            else:                
                out.append('"%s" : already present'%fileInFolder)       
        return '\n'.join(out)
    except Exception, message:
        out.append(fileInFolder + " : %s"%message)
        return '\n'.join(out)   

        

     
