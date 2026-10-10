# SPDX-License-Identifier: Apache-2.0
import copy
class Chaining:
 def __init__(self,policy,mode):
  self.buckets=[[],[]];self.n=0;self.policy=policy;self.mode=mode
 def step(self,op):
  name,key=op[:2]
  if name not in ['put','find','delete'] or type(key) is not int or not -32<=key<=48:raise ValueError('operation/key')
  if len(op)!=(3 if name=='put' else 2):raise ValueError('operation arity')
  if name=='put' and (type(op[2]) is not str or not 1<=len(op[2])<=2 or any(not 'A'<=v<='Z' for v in op[2])):raise ValueError('value')
  before=copy.deepcopy(self.buckets);n_before=self.n;m=len(self.buckets);bucket=key%m;chain=self.buckets[bucket];visited=[];match=None
  for i,(k,v) in enumerate(chain):
   visited.append(k)
   if k==key:match=i;break
  found=match is not None;value=chain[match][1] if found else None;action=name; moves=[]
  if name=='put':
   value=op[2];action='update' if found else 'insert'
   if found:chain[match]=[key,value]
   else:chain.append([key,value]);self.n+=1
   if not found and self.policy=='doubling' and self.n>m:
    old=self.buckets;self.buckets=[[] for _ in range(m*2)]
    for source,items in enumerate(old):
     for k,v in items:
      dest=k%(m*2);self.buckets[dest].append([k,v]);moves.append(dict(key=k,value=v,old_bucket=source,new_bucket=dest))
  elif name=='delete' and found:
   if self.mode=='delete-whole-bucket':self.n-=len(chain);chain.clear()
   else:del chain[match];self.n-=1
  return dict(operation=op,before=before,n_before=n_before,capacity_before=m,bucket=bucket,visited_keys=visited,key_comparisons=len(visited),found=found,value=value,action=action,rehash_moves=moves,move_count=len(moves),after=copy.deepcopy(self.buckets),n_after=self.n,capacity_after=len(self.buckets))
