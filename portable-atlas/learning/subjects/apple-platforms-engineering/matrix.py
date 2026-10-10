"""Finite cross-product JSON inputs authored independently of Swift outputs."""
import itertools,json
def cases():
 missing=object();names=[missing,None,7,'Aki',''];ages=[missing,None,True,'7',-128,127,128,7.5];notes=[missing,None,'memo',7];out=[]
 for i,(name,age,note) in enumerate(itertools.product(names,ages,notes)):
  data={k:v for k,v in [('name',name),('age',age),('note',note)] if v is not missing}
  out.append({'id':'matrix-'+str(i),'json':json.dumps(data,separators=(',',':'))})
 return out
