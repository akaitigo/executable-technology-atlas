import json,sys
FIXED={'uid':1000,'gid':10,'supplementary':[20]}
def rejected(reason):return {'observed':False,'result':'REFUSED','allowed':None,'firstStop':None,'gates':[],'reason':reason},2
def run(x):
 if not isinstance(x,dict) or set(x)!={'path','principal','security','algorithm','inodes'}:return rejected('invalid request')
 p=x['principal']
 if not isinstance(p,dict) or p.get('uid')==0:return rejected('unsupported privileged principal')
 if p!=FIXED:return rejected('fixed nonprivileged principal required')
 if x['security']!='ordinary':return rejected('unsupported security layer')
 if x['algorithm'] not in ('walk','leaf-only') or x['path'] not in ('/vault/report','/missing/report','/vault/missing'):return rejected('unsupported path or algorithm')
 nodes=x['inodes']
 if not isinstance(nodes,dict) or set(nodes)!={'/','/vault','/vault/report'}:return rejected('invalid inode table')
 for n in nodes.values():
  if not isinstance(n,dict) or set(n)!={'kind','uid','gid','mode'} or n['kind'] not in ('directory','file'):return rejected('unsupported inode kind')
  if any(type(n[k]) is not int or not 0<=n[k]<=65535 for k in ('uid','gid')):return rejected('invalid inode owner')
  m=n['mode']
  if not isinstance(m,str) or len(m)!=4 or m[0]!='0' or any(c not in '01234567' for c in m):return rejected('invalid permission bits')
 if nodes['/']['kind']!='directory':return rejected('root directory required')
 trace=[]
 def result(label,stop=None):return {'observed':True,'result':label,'allowed':label=='ALLOW','firstStop':stop,'gates':trace},0
 def permission(node,stage,bit):
  n=nodes[node]
  cls='owner' if p['uid']==n['uid'] else 'group' if n['gid'] in [p['gid']]+p['supplementary'] else 'other'
  shift={'owner':6,'group':3,'other':0}[cls];bits=(int(n['mode'],8)>>shift)&7;ok=(bits&bit)==bit
  trace.append({'stage':stage,'node':node,'selectedClass':cls,'selectedBits':format(bits,'03b'),'required':'x' if bit==1 else 'r','passed':ok,'kind':None})
  return ok
 def lookup(node,intermediate):
  n=nodes.get(node);ok=n is not None and (not intermediate or n['kind']=='directory')
  trace.append({'stage':'LOOKUP','node':node,'selectedClass':None,'selectedBits':None,'required':None,'passed':ok,'kind':n['kind'] if n else None})
  return 'ENOENT' if n is None else 'ENOTDIR' if not ok else None
 parts=x['path'].split('/')[1:];current='/'
 if x['algorithm']=='leaf-only':
  e=lookup(x['path'],False)
  if e:return result(e,{'node':x['path'],'stage':'LOOKUP'})
 else:
  for i,component in enumerate(parts):
   if not permission(current,'SEARCH',1):return result('EACCES',{'node':current,'stage':'SEARCH'})
   nextnode=('/' if current=='/' else current+'/')+component;e=lookup(nextnode,i<len(parts)-1)
   if e:return result(e,{'node':nextnode,'stage':'LOOKUP'})
   current=nextnode
 if not permission(x['path'],'READ',4):return result('EACCES',{'node':x['path'],'stage':'READ'})
 return result('ALLOW')
if __name__=='__main__':
 try:x=json.load(sys.stdin)
 except json.JSONDecodeError as e:print('JSONDecodeError: '+str(e),file=sys.stderr);sys.exit(3)
 try:o,code=run(x)
 except Exception as e:print(type(e).__name__+': '+str(e),file=sys.stderr);sys.exit(4)
 print(json.dumps(o));sys.exit(code)
