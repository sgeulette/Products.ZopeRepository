{'title':'',}
## Script (Python) "decoratePlonesiteProductView"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=installed_version, inst_local_version
##title=
##
# passed parameters : installed_version, inst_local_version

version_cl = ''

if installed_version != inst_local_version:
  version_cl = 'red'

return {'ver_cl':version_cl}
