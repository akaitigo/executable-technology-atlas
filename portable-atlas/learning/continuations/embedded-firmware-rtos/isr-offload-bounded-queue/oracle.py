"""Literal table fixed before producer: no shared queue implementation."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TABLE=json.loads((ROOT/'oracle.json').read_text())
FIXTURE=json.loads((ROOT/'fixture.json').read_text())
def validate(raw):
 assert raw['fixture']==FIXTURE
 assert [r['case'] for r in raw['cases']]==[c['id'] for c in FIXTURE['cases']]
 for c,r in zip(FIXTURE['cases'],raw['cases']):
  e=TABLE['expected'][c['id']];assert r['input']==c
  for key in ['status','reason','timeline','counts']:assert r[key]==e[key],(c['id'],key)
  if r['timeline'] is None:continue
  for row in r['timeline']:
   a=set(row['arrived']);s=set(row['accepted']);d=set(row['dropped']);p=set(row['processed']);q=set(row['queue']);lost=set(row['lost'])
   assert a==s|d and not s&d and s==p|q|lost and not p&q and not p&lost and not q&lost
   assert set(map(int,row['completions']))==p
   assert len(row['queue'])<=c['capacity']
 return dict(cases=len(raw['cases']),literal_tick_rows=36,shared_queue_function=False,real_IRQ=False)
