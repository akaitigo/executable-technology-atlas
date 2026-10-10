"""Read-only exact geometry/table/binding verifier; explicit binding update only."""
import json,re,hashlib,argparse
from fractions import Fraction as F
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from producer import evaluate,sampled_bad
from oracle import expected,distance_squared
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def binding():return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='binding.json' and '__pycache__' not in p.parts}
def verify():
 ptr=json.loads((ROOT/'evidence/current.json').read_text());p=ROOT/'evidence'/ptr['raw'];assert sha(p)==ptr['sha256'];r=json.loads(p.read_text());f=json.loads((ROOT/'fixture.json').read_text());assert r['fixture']==f and r['input_sha256']==sha(ROOT/'fixture.json')
 for n,h in r['source_sha256'].items():assert sha(ROOT/n)==h,('source drift',n)
 table={'narrow-width1':['CLEAR','CLEAR','COLLISION','COLLISION'],'wide-width2':['CLEAR']*4,'missed-middle':['COLLISION']*4};d2={'narrow-width1':'1/4','wide-width2':'1','missed-middle':'0'};assert len(r['cases'])==12
 for c in r['cases']:
  scene=next(s for s in f['scenes'] if s['id']==c['scene']);normal=evaluate(scene,c['radius']);o=expected(scene,c['radius']);bad=sampled_bad(scene,c['radius'],f['bad_samples']);assert c['producer']==normal and c['oracle']==o and c['intentional_bad']==bad
  assert normal['status']==o['status']==table[scene['id']][f['radii'].index(c['radius'])];assert o['distance_squared']==d2[scene['id']]
  assert bad['status']==('CLEAR' if scene['id']=='missed-middle' else normal['status'])
  # Equivalent route reversal and subdivision with independent distances.
  rev=dict(scene,route=list(reversed(scene['route'])));assert evaluate(rev,c['radius'])['status']==normal['status'] and expected(rev,c['radius'])==o
  middle=['2','0'];left=dict(scene,route=[scene['route'][0],middle]);right=dict(scene,route=[middle,scene['route'][1]])
  split_collision=any(expected(s,c['radius'])['status']=='COLLISION' for s in (left,right));assert split_collision==(normal['status']=='COLLISION')
 # Hand-computed rounded-corner check; expanded box would spuriously reject.
 corner=dict(route=[['0','0'],['1','0']],obstacles=[['7/5','2/5','2','1']]);assert distance_squared(corner['route'],corner['obstacles'][0])==F(8,25)
 assert evaluate(corner,'1/2')['status']==expected(corner,'1/2')['status']=='CLEAR';assert evaluate(corner,'3/4')['status']==expected(corner,'3/4')['status']=='COLLISION'
 assert r['outcome_counts']==dict(completed_evaluations=12,collision_refusals=6,clear_routes=6,execution_failures=0) and r['exit_code']==0
 for t in ('footprint','verify','diagram','sources'):assert route(t)['status']=='supported' and (ROOT/route(t)['target']).exists()
 for t in ('ros','real-robot','polygon-pose','safety','new-planner'):assert route(t)['status']=='unsupported'
 links=0
 for path in (ROOT/'README.md',ROOT/'SOURCES.md',ROOT/'EXPECTATIONS.md',ROOT/'skills/atlas-footprint-clearance/SKILL.md',ROOT/'index.html'):
  text=path.read_text();refs=re.findall(r'\]\(([^)]+)\)',text) if path.suffix=='.md' else re.findall(r'(?:href|src)="([^"]+)"',text)
  for ref in refs:
   if ref.startswith(('http','#')):continue
   u=urlsplit(ref);assert (path.parent/u.path).exists(),(path.name,ref)
   for n in parse_qs(u.query).get('file',[]):assert (ROOT/n).is_file(),n
   links+=1
 qa=json.loads((ROOT/'evidence/ui-qa.json').read_text());assert qa['status']=='passed' and qa['raw_sha256']==sha(p) and qa['owned_cleanup'] is True
 assert json.loads((ROOT/'evidence/binding.json').read_text())==binding(),'artifact drift'
 return dict(status='passed',clear_routes=6,expected_collision_refusals=6,execution_failures=0,exact_contact_boundary='radius1/2 refused in width1',sampling_counterexample='middle obstacle; 4 radii',rounded_corner_hand_check=True,route_reversal_subdivision=True,route_checks='4 supported / 5 unsupported',local_links=links,whole_subject_complete=False,real_robot_ROS='not executed')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--record-binding',action='store_true');a=p.parse_args()
 if a.record_binding:(ROOT/'evidence/binding.json').write_text(json.dumps(binding(),indent=2)+'\n')
 try:print(json.dumps(verify(),ensure_ascii=False,indent=2))
 except (AssertionError,ValueError,KeyError,FileNotFoundError) as e:print(json.dumps(dict(status='failed',reason=str(e))));raise SystemExit(1)
