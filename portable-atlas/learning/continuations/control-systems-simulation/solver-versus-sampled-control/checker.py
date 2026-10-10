"""Focused saved-run verification, default read-only. No recorder invocation."""
import json,math,hashlib,argparse,re
from decimal import Decimal,localcontext
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
from models import simulate
from oracle import expected
from route import route
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def binding():return {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(ROOT.rglob('*')) if p.is_file() and p.name!='binding.json' and '__pycache__' not in p.parts}
def near(a,b):assert math.isfinite(a) and abs(a-float(b))<=2e-12*max(1,abs(float(b))),(a,b)
def verify():
 ptr=json.loads((ROOT/'evidence/current.json').read_text());p=ROOT/'evidence'/ptr['raw'];assert sha(p)==ptr['sha256'];raw=json.loads(p.read_text());fixture=json.loads((ROOT/'fixture.json').read_text());assert raw['fixture']==fixture and raw['input_sha256']==sha(ROOT/'fixture.json')
 for name,h in raw['source_sha256'].items():assert sha(ROOT/name)==h,('source drift',name)
 assert len(raw['cases'])==16;points=0;maxdiff={}
 for c in raw['cases']:
  r=c['result'];o=expected(c['h'],c['model']);assert c['oracle']==o and r==simulate(c['h'],c['model']);assert r['T']==8 and r['N']*Decimal(c['h'])==8
  assert len(r['points'])==r['N']+1 and len(r['intervals'])==r['N'];near(r['a'],o['a']);near(r['points'][1]['y'],o['initial_step']);near(r['continuous_reference'],o['continuous_T'])
  for point,y,u in zip(r['points'],o['ys'],o['u_at_state']):near(point['y'],y);near(point['u_at_state'],u);points+=1
  near(r['signed_difference'],Decimal(o['ys'][-1])-Decimal(o['continuous_T']))
  for n,i in enumerate(r['intervals']):
   near(i['y_next'],o['ys'][n+1]);near(i['t1']-i['t0'],c['h'])
   if c['model']=='sampled-hold-exact':near(i['u_used'],o['u_at_state'][n]);assert i['y_mid'] is not None
   if c['model'] in ('continuous-exact','sampled-hold-exact'):
    with localcontext() as ctx:
     ctx.prec=80;half=Decimal(c['h'])/2
     if c['model']=='continuous-exact':assert i['u_used'] is None;mid=Decimal(2)/3*(1-(-3*(Decimal(n)*Decimal(c['h'])+half)).exp())
     else:mid=(-half).exp()*Decimal(o['ys'][n])+(1-(-half).exp())*Decimal(o['u_at_state'][n])
     near(i['y_mid'],mid)
   elif c['model']=='backward-euler':near(i['u_used'],o['u_at_state'][n+1])
   elif c['model']=='forward-euler':near(i['u_used'],o['u_at_state'][n])
   else:assert i['u_used'] is None
  maxdiff[(c['h'],c['model'])]=max(abs(p['y']-2/3*(-math.expm1(-3*p['t']))) for p in r['points'])
 # Hand-fixed first forward/backward steps, separate from general closed form.
 hand={'0.1':(.2,2/13),'0.2':(.4,1/4),'0.8':(1.6,8/17),'1.6':(3.2,16/29)}
 for h,(f,b) in hand.items():near(simulate(h,'forward-euler')['points'][1]['y'],f);near(simulate(h,'backward-euler')['points'][1]['y'],b)
 assert simulate('0.8','forward-euler')['behavior']=='unstable' and simulate('0.8','sampled-hold-exact')['behavior']=='stable'
 assert simulate('1.6','sampled-hold-exact')['behavior']=='unstable' and simulate('1.6','backward-euler')['behavior']=='stable'
 for m in ('forward-euler','backward-euler','sampled-hold-exact'):assert maxdiff[('0.1',m)]<maxdiff[('0.2',m)]
 # Reject false same-model claims using independent oracle, not labels.
 assert expected('0.8','sampled-hold-exact')['ys'][1]!=expected('0.8','continuous-exact')['ys'][1]
 assert float(expected('1.6','sampled-hold-exact')['a']) < -1 < float(expected('1.6','backward-euler')['a'])
 for t in ('sampling','verify','timeline','sources'):assert route(t)['status']=='supported' and (ROOT/route(t)['target']).exists()
 for t in ('hil','real-plant','pid','safety','custom-gain'):assert route(t)['status']=='unsupported'
 links=0
 for f in (ROOT/'README.md',ROOT/'SOURCES.md',ROOT/'DERIVATION.md',ROOT/'skills/atlas-solver-sampling/SKILL.md',ROOT/'index.html'):
  text=f.read_text();refs=re.findall(r'\]\(([^)]+)\)',text) if f.suffix=='.md' else re.findall(r'(?:href|src)="([^"]+)"',text)
  for ref in refs:
   if ref.startswith(('http','#')):continue
   parsed=urlsplit(ref);assert (f.parent/parsed.path).exists(),(f.name,ref)
   for n in parse_qs(parsed.query).get('file',[]):assert (ROOT/n).is_file(),n
   links+=1
 qa=json.loads((ROOT/'evidence/ui-qa.json').read_text());assert qa['status']=='passed' and qa['raw_sha256']==sha(p) and qa['owned_cleanup'] is True
 assert json.loads((ROOT/'evidence/binding.json').read_text())==binding(),'artifact drift'
 return dict(status='passed',fixed_T=8,conditions=16,independent_state_u_points=points,initial_hand_steps='matched',small_h_transient_difference='decreases for .1 versus .2, sample grid only',route_checks='4 supported / 5 unsupported',local_links=links,whole_subject_complete=False,real_plant_HIL='unrun')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--record-binding',action='store_true');a=p.parse_args()
 if a.record_binding:(ROOT/'evidence/binding.json').write_text(json.dumps(binding(),indent=2)+'\n')
 try:print(json.dumps(verify(),ensure_ascii=False,indent=2))
 except (AssertionError,ValueError,KeyError,FileNotFoundError) as e:print(json.dumps(dict(status='failed',reason=str(e))));raise SystemExit(1)
