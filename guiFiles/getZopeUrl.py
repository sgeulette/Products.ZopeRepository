{'title':'',}
## Script (Python) "getZopeUrl"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=servername, port
##title=
##
zopeurl = ''
if servername.startswith('villesetcommunes'):
  zopeurl = 'http://%s.all2all.org:%s'%(servername, port)
elif servername.startswith('plonegov'):
  zopeurl = 'http://plonegov-%s.proxy.pilotsystems.net'%(port)
else:
  zopeurl = 'http://%s:%s'%(servername, port)
return zopeurl
