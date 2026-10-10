# SPDX-License-Identifier: Apache-2.0
# No import of Chaining, no hash, no bucket storage.
def list_trace(operations):
 entries=[];rows=[]
 for op in operations:
  name,key=op[:2];hit=next((i for i,pair in enumerate(entries) if pair[0]==key),None)
  found=hit is not None;value=entries[hit][1] if found else None;action=name
  if name=='put':
   value=op[2];action='update' if found else 'insert'
   if found:entries[hit]=[key,value]
   else:entries.append([key,value])
  elif name=='delete' and found:del entries[hit]
  rows.append(dict(found=found,value=value,action=action,entries=sorted([p[:] for p in entries])))
 return rows
