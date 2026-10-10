"""Explicit unique-run recorder; normal invocation reads evidence only."""
import json,datetime,uuid,hashlib,platform,sys,argparse
from pathlib import Path
from producer import evaluate,sampled_bad
from oracle import expected
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record():
 fixture=json.loads((ROOT/'fixture.json').read_text());cases=[]
 for scene in fixture['scenes']:
  for radius in fixture['radii']:
   cases.append(dict(scene=scene['id'],radius=radius,producer=evaluate(scene,radius),oracle=expected(scene,radius),intentional_bad=sampled_bad(scene,radius,fixture['bad_samples'])))
 return dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command='python3 -B record.py --record',exit_code=0,attempt='Fraction C-space inflated primitive execution; independent original-obstacle distance oracle',environment=dict(python=platform.python_version(),system=platform.system(),release=platform.release(),machine=platform.machine(),arithmetic='stdlib fractions.Fraction; exact rational boundaries'),fixture=fixture,input_sha256=sha(ROOT/'fixture.json'),source_sha256={n:sha(ROOT/n) for n in ('fixture.json','EXPECTATIONS.md','producer.py','oracle.py','record.py')},cases=cases,outcome_counts=dict(completed_evaluations=len(cases),collision_refusals=sum(c['producer']['status']=='COLLISION' for c in cases),clear_routes=sum(c['producer']['status']=='CLEAR' for c in cases),execution_failures=0),unrun=['real robot/ROS','polygon orientation','sensor/pose error','braking','safety guarantee','planner'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
 if a.record:
  name='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
  try:
   raw=record()
   with (ROOT/'evidence'/name).open('x') as out:json.dump(raw,out,ensure_ascii=False,indent=2);out.write('\n')
   (ROOT/'evidence/current.json').write_text(json.dumps(dict(raw=name,sha256=sha(ROOT/'evidence'/name)),indent=2)+'\n');print(name)
  except Exception as e:
   with (ROOT/'evidence'/('failed-'+uuid.uuid4().hex+'.json')).open('x') as out:json.dump(dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),command='python3 -B record.py --record',exit_code=1,error=repr(e)),out)
   raise
 else:
  p=json.loads((ROOT/'evidence/current.json').read_text());print((ROOT/'evidence'/p['raw']).read_text())
