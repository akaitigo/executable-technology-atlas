"""Explicit observation recorder. Each record gets a fresh UTC/UUID file; never overwrites raw."""
import argparse,json,datetime,platform,sys,uuid,hashlib
from pathlib import Path
from models import simulate
from oracle import expected
ROOT=Path(__file__).resolve().parent
SOURCES=('fixture.json','DERIVATION.md','models.py','oracle.py','record.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def observe():
 f=json.loads((ROOT/'fixture.json').read_text());cases=[]
 for h in f['steps']:
  for m in f['models']:
   result=simulate(h,m);o=expected(h,m);cases.append(dict(h=h,model=m,result=result,oracle=o))
 return dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),attempt='explicit record; float recurrence and independent Decimal80 closed form',command='python3 -B record.py --record',environment=dict(system=platform.system(),release=platform.release(),machine=platform.machine(),python=platform.python_version(),float_mant_dig=sys.float_info.mant_dig,oracle_decimal_precision=80),fixture=f,input_sha256=sha(ROOT/'fixture.json'),source_sha256={n:sha(ROOT/n) for n in SOURCES},cases=cases,limits=['mathematical CPU model only','no plant/HIL/PID entirety','no safety guarantee','critical boundary time series not executed'])
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args()
 if a.record:
  name='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
  try:
   data=observe()
   with (ROOT/'evidence'/name).open('x') as stream:json.dump(data,stream,indent=2);stream.write('\n')
   (ROOT/'evidence/current.json').write_text(json.dumps({'raw':name,'sha256':sha(ROOT/'evidence'/name)},indent=2)+'\n');print(name)
  except Exception as e:
   with (ROOT/'evidence'/('failed-'+uuid.uuid4().hex+'.json')).open('x') as stream:json.dump({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'error':repr(e)},stream)
   raise
 else:
  ptr=json.loads((ROOT/'evidence/current.json').read_text());print((ROOT/'evidence'/ptr['raw']).read_text())
