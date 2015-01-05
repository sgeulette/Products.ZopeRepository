{'title':'',}
## Script (Python) "decorateMountpointView"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=mp_size, inst_id, mp_id
##title=
##
# passed parameters : mp_size, inst_id, mp_id

size_cl = ''

if mp_size > 2000:
  size_cl = 'red'
elif mp_size > 1250:
  size_cl = 'orange'
elif mp_size > 500:
  size_cl = 'green'

plonesites = []
rows = context.select_plonesites_for_mountpoint(inst_id=inst_id,mp_id=mp_id)
for row in rows:
  plonesites.append(row[0])

return {'size_cl':size_cl, 'plonesites':'<br />'.join(plonesites)}
