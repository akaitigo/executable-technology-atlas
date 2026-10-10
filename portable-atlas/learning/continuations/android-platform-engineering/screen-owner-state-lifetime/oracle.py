"""Literal identities/generation/state; no producer import or transition replay."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TABLE=json.loads((ROOT/'oracle.json').read_text())
FIXTURE=json.loads((ROOT/'fixture.json').read_text())
def project(row):
 owners=row['owners'];assert set(owners)<= {'A','B'}
 def item(screen):
  if screen not in owners:return None
  v=owners[screen];assert set(v)=={'owner','view_generation','state'};assert type(v['state']) is int and 0<=v['state']<=9 and type(v['view_generation']) is int and v['view_generation']>=1
  return [v['owner'],v['view_generation'],v['state']]
 return [row['process'],row['alive'],item('A'),item('B')]
def validate(raw):
 assert raw['fixture']==FIXTURE and [r['case'] for r in raw['cases']]==[c['id'] for c in FIXTURE['cases']]
 for c,r in zip(FIXTURE['cases'],raw['cases']):
  e=TABLE['expected'][c['id']];assert r['input']==c and r['status']==e['status'] and r['reason']==e['reason'],c['id']
  if e['rows'] is None:assert r['timeline'] is None and r['final'] is None;continue
  assert [project(row) for row in r['timeline']]==e['rows'],c['id']
  assert r['final']==r['timeline'][-1]
  for i,row in enumerate(r['timeline']):assert row['step']==i and row['event']==(None if i==0 else c['events'][i-1])
 return dict(cases=len(raw['cases']),literal_owner_rows=26,shared_transition=False,real_Android=False)
