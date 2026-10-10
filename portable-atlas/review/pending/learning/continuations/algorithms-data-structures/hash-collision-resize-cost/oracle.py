# SPDX-License-Identifier: Apache-2.0
from cases import HAND,FIXTURES
from list_oracle import list_trace
# Expected fault divergence sets fixed by hand, not by implementation.
FAULT={'collision':{'fixed':[6,7,8,9],'doubling':[]},'distributed':{'fixed':[8,9],'doubling':[]},'persistent':{'fixed':[],'doubling':[]},'threshold':{'fixed':[],'doubling':[]},'negative':{'fixed':[4,5,6],'doubling':[4,5,6]},'empty':{'fixed':[],'doubling':[]}}
def logical(buckets):return sorted([p for chain in buckets for p in chain])
def residue(key,m):return key-(key//m)*m
def check(r):
 assert r['status']=='EXECUTED';c=r['inputs'];ops=FIXTURES[c['fixture']];expected=list_trace(ops);rows=r['trace'];assert len(rows)==len(ops) and r['oracle']==expected
 prev=[[],[]];n=0;diff=[]
 for i,(row,op,want) in enumerate(zip(rows,ops,expected)):
  assert row['step']==i+1 and row['operation']==op and row['before']==prev and row['capacity_before']==len(prev) and row['n_before']==n
  name,key=op[:2];m=len(prev);b=residue(key,m);assert row['bucket']==b
  chain=prev[b];hit=next((j for j,p in enumerate(chain) if p[0]==key),None)
  visited=[p[0] for p in chain[:hit+1]] if hit is not None else [p[0] for p in chain]
  assert row['visited_keys']==visited and row['key_comparisons']==len(visited)
  found=hit is not None;value=op[2] if name=='put' else (chain[hit][1] if found else None);action=('update' if found else 'insert') if name=='put' else name
  assert row['found']==found and row['value']==value and row['action']==action
  # Independently update flat dictionary semantics; fault loses the matching chain.
  flat=logical(prev)
  if name=='put':flat=sorted([p for p in flat if p[0]!=key]+[[key,op[2]]])
  elif name=='delete' and found:flat=[p for p in flat if (residue(p[0],m)!=b if c['mode']=='delete-whole-bucket' else p[0]!=key)]
  n=len(flat);grow=name=='put' and not found and c['policy']=='doubling' and n>m;new_m=2*m if grow else m
  assert row['capacity_after']==new_m and row['n_after']==n and len(row['after'])==new_m and logical(row['after'])==flat
  assert len({p[0] for p in flat})==len(flat)
  for j,items in enumerate(row['after']):assert all(residue(p[0],new_m)==j for p in items)
  pre_growth=[p[:] for bucket in prev for p in bucket]
  if name=='put' and not found:pre_growth.append([key,op[2]])
  if grow:
   # Traverse the old buckets with the newly inserted key at its own bucket tail.
   ordered=[p for j,items in enumerate(prev) for p in (items+([[key,op[2]]] if j==b else []))]
   want_moves=[dict(key=k,value=v,old_bucket=residue(k,m),new_bucket=residue(k,new_m)) for k,v in ordered]
  else:want_moves=[]
  assert row['rehash_moves']==want_moves and row['move_count']==len(want_moves)
  actual=dict(found=found,value=value,action=action,entries=flat);match=actual==want
  assert row['actual_logical']==actual and row['list_oracle']==want and row['logical_match']==match
  if not match:diff.append(i+1)
  prev=row['after']
 assert r['differences']==diff and r['total_comparisons']==sum(x['key_comparisons'] for x in rows) and r['total_moves']==sum(x['move_count'] for x in rows)
 assert r['final_capacity']==len(prev) and r['final_entries']==logical(prev)
 hand=next(x for x in HAND['fixtures'] if x['id']==c['fixture'])
 if c['mode']=='normal':
  assert diff==[] and r['total_comparisons']==hand['normal_comparisons'][c['policy']] and r['total_moves']==hand['normal_moves'][c['policy']] and r['final_capacity']==hand['normal_final_capacity'][c['policy']]
 else:assert diff==FAULT[c['fixture']][c['policy']]
