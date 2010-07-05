{'title':'',}
## Script (Python) "getVirtualhostRewritesLines"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=servername,rewrites
##title=
##
lines = []
for rewrite in rewrites:
  zopeurl = context.getZopeUrl(servername,rewrite['port'])
  lines.append('<a target="_blank" href="%s/manage_main">%s</a>'%(zopeurl, rewrite['port']) + ' | ' + '<a target="_blank" href="%s%s/manage_main">%s</a>'%(zopeurl, rewrite['inst_path'], rewrite['inst_path']))
return ','.join(lines)
