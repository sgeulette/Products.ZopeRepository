{'title':'',}
## Script (Python) "decorateInstanceView"
##bind container=container
##bind context=context
##bind namespace=
##bind script=script
##bind subpath=traverse_subpath
##parameters=local_version,repository_version,local_revision,repository_revision,svn_diff,repository_address
##title=
##
# passed parameters :local_version,repository_version,local_revision,repository_revision,svn_diff,repository_address

rep_version_cl = rep_rev_cl = diff_cl = ''
diff_value = svn_diff
trac = {'svn.communesplone.org/svn':'http://dev.communesplone.org/trac', 
        'svn.plone.org/svn/collective':'http://dev.plone.org/collective',
        'svn.plone.org/svn/archetypes':'http://dev.plone.org/archetypes',
#        'svn.quintagroup.com/products':'http://projects.quintagroup.com/products',  #doesn't provide a changeset
        }

# si url et pas rep_svn => couleur rouge sur rep_version
# si rev != et diff = No => couleur verte sur diff
# si rev != et diff = Yes => couleur rouge sur diff
if repository_address:
  if not repository_revision:
    rep_rev_cl = 'red'
  elif repository_revision != local_revision:
    if svn_diff == 'No':
      rep_rev_cl = diff_cl = 'green'
    elif svn_diff == 'Yes':
      rep_rev_cl = diff_cl = 'red'

# si versions != => couleur rouge sur rep_version
if repository_version and local_version != repository_version:
  rep_version_cl = 'red'

diff_href = ''
if svn_diff and svn_diff != 'No':
  temp = repository_address
  if temp.startswith('http://'):
    temp = temp[7:]
  elif temp.startswith('https://'):
    temp = temp[8:]
  else:
    temp = 'error_in_repository_address'
  for domain in trac.keys():
    if temp.startswith(domain):
      temp = temp.replace(domain+'/', '')
      temp = temp.replace('/', '%2F')
      temp = trac[domain]+'/changeset?new='+str(repository_revision)+'%40'+temp+'&old='+str(local_revision)+'%40'+temp
      break
  if temp.find('changeset') >= 0:
    diff_href = temp

return {'ver_cl':rep_version_cl, 'rev_cl':rep_rev_cl, 'diff_cl':diff_cl, 'diff_href':diff_href}
