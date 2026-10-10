"""Literal terminals, sRGB and CSS only; no resolver traversal implementation."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIXTURE=json.loads((ROOT/'fixture.json').read_text());TABLE=json.loads((ROOT/'oracle.json').read_text())
def validate(raw):
 assert raw['fixture']==FIXTURE and [c['case'] for c in raw['cases']]==list(TABLE['expected']);normal=0
 for r,c in zip(raw['cases'],FIXTURE['cases']):
  expected=TABLE['expected'][c['id']];assert r['input']==c
  for key in ['status','reason','css','resolved']:assert r[key]==expected[key],(c['id'],key)
  if r['css'] is None:assert r['resolved'] is None;continue
  normal+=1;direct=[['semantic.action','primitive.green' if c['id']=='alias-green' else 'primitive.blue'],['semantic.focus','semantic.action'],['semantic.positive','primitive.green']]
  assert [[e['token'],e['target']] for e in r['trace'] if e['action']=='reference']==direct
  assert {e['token']:e['terminal'] for e in r['trace'] if e['action']=='resolved'}=={n:t['terminal'] for n,t in expected['resolved'].items()}
 return dict(cases=len(raw['cases']),generated_css_cases=normal,handwritten_terminals_srgb_css=True,resolver_shared=False,full_DTCG_conformance=False)
def computed_expected(case):return TABLE['expected'][case]['computed']
