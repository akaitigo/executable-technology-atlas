import json,sys,uuid,hashlib
from pathlib import Path
from execute import execute,utc
from oracle import check
P=Path(__file__).resolve().parent
fixtures=json.loads((P/'fixture.json').read_text());literals=json.loads((P/'oracle.json').read_text());custom=json.loads((P/'custom-oracle.json').read_text())
def collect():
 attempts=[];failures=[]
 for c in fixtures+custom:
  raw=execute(json.dumps(c['input']),c.get('inject_failure',False))
  try:check(raw['result'],c['input'],literals.get(c['id'],c.get('literal')))
  except Exception as e:failures.append(dict(id=c['id'],reason=type(e).__name__))
  if raw['audit'] and raw['audit']['exit']!=0:failures.append(dict(id=c['id'],reason='audit failed'))
  attempts.append(dict(id=c['id'],raw=raw))
 return dict(status='failed' if failures else 'passed',failures=failures,started=attempts[0]['raw']['started'],completed=utc(),attempts=attempts)
if __name__=='__main__':
 if sys.argv[1:] in [[],['--record']]:
  report=collect()
  if sys.argv[1:]:
   name='run-'+utc().split('.')[0].replace('-','').replace(':','')+'-'+uuid.uuid4().hex[:8]+'.json';f=P/'evidence'/name;f.write_text(json.dumps(report,indent=2)+'\n')
   if report['status']=='passed':(P/'evidence/current.json').write_text(json.dumps(dict(raw=name,sha256=hashlib.sha256(f.read_bytes()).hexdigest()),indent=2)+'\n')
   print(json.dumps(dict(status=report['status'],raw=name,cases=len(report['attempts']),failures=report['failures'])))
  else:print(json.dumps(dict(status=report['status'],cases=len(report['attempts']),failures=report['failures'])))
  sys.exit(0 if report['status']=='passed' else 1)
 c=next((c for c in fixtures if c['id']==sys.argv[1]),None)
 if c is None:print(json.dumps(dict(status='INPUT_REFUSED',reason='UNKNOWN_CASE')));sys.exit(2)
 raw=execute(sys.argv[2] if len(sys.argv)>2 else json.dumps(c['input']),c.get('inject_failure',False));print(json.dumps(raw));sys.exit(raw['exit'])
