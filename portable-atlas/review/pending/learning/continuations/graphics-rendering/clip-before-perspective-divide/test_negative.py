import copy,json,sys,subprocess
from pathlib import Path
from oracle import check
P=Path(__file__).resolve().parent

def collect():
 raw=json.loads((P/'evidence'/json.loads((P/'evidence/current.json').read_text())['raw']).read_text());base=raw['attempts'][0]['raw'];out=base['result'];inp=json.loads(base['input_json']);mutants=[]
 for field,value in [('inside',[True]*3),('intersections',[])]:
  m=copy.deepcopy(out);m[field]=value;mutants.append((field,m))
 for name in ['near_clip','no_clip','drop_outside']:
  for field,value in [('area','99'),('signed_area','99'),('state','FALSE'),('ndc',[]),('polygon',[]),('fan_signed_areas',['99']),('fan',[[9,8,7]])]:
   m=copy.deepcopy(out);m['strategies'][name][field]=value;mutants.append((name+'/'+field,m))
 detected=[]
 for name,m in mutants:
  try:check(m,inp)
  except AssertionError:detected.append(name)
 invalid=[]
 for name,x,reason in [('bool',{'vertices':[[True,'0','0','1']]*3},'COMPONENT'),('zero-denominator',{'vertices':[['1/0','0','0','1']]*3},'COMPONENT'),('float',{'vertices':[[0.5,'0','0','1']]*3},'COMPONENT'),('extra',dict(inp,extra=1),'SCHEMA'),('shape',{'vertices':[]},'SCHEMA'),('large',{'vertices':[['21','0','0','1']]*3},'COMPONENT'),('negative-denominator',{'vertices':[['1/-2','0','0','1']]*3},'COMPONENT'),('malformed-json',None,'SCHEMA')]:
  s=json.dumps(x) if x is not None else '{';r=subprocess.run([sys.executable,'-B','model.py'],cwd=P,input=s,text=True,capture_output=True);o=json.loads(r.stdout);invalid.append(dict(id=name,exit=r.returncode,result=o,passed=r.returncode==2 and o==dict(status='INPUT_REFUSED',reason=reason)))
 return dict(status='passed' if len(detected)==len(mutants) and all(x['passed'] for x in invalid) else 'failed',mutants=len(mutants),detected=detected,schema=invalid)
if __name__=='__main__':
 r=collect()
 if sys.argv[1:]==['--record']:(P/'evidence/negative.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r));sys.exit(0 if r['status']=='passed' else 1)
