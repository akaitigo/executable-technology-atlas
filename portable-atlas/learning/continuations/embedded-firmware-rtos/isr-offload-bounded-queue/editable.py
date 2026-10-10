"""Fixed editable subsets; fresh actual children, read-only validation by default."""
import json,subprocess,datetime,uuid,hashlib,argparse,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TABLE=json.loads((ROOT/'editable-oracle.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def validate(raw):
 assert [x['id'] for x in raw['attempts']]==[c['id'] for c in TABLE['cases']]
 for c,a in zip(TABLE['cases'],raw['attempts']):
  args=['python3','-B','runner.py','--case',c['case'],'--events-json',json.dumps(c['events'],separators=(',',':'))];assert a['command']==args and a['exit']==0 and not a['stderr'];r=json.loads(a['stdout']);assert r['case']==c['case'] and r['input']['events']==c['events']
  for k,v in c['expected'].items():assert r[k]==v,(c['id'],k)
  assert datetime.datetime.fromisoformat(a['ended_utc'])>=datetime.datetime.fromisoformat(a['started_utc'])
 return dict(editable_cases=8,literal_tick_rows=48)
def answer_check(x,r):
 c=r['counts'];last=r['timeline'][-1]
 for key,label in [('arrived','到着'),('accepted','受入'),('dropped','drop'),('processed','完了'),('lost','受入後喪失')]:assert label+str(c[key])+'件' in x['answer'],(key,x['answer'])
 for key,label in [('lost','喪失ID '),('processed','処理完了ID '),('completions','完了tick ')]:assert label+json.dumps(last[key],separators=(',',':')) in x['answer']
def verify_ui(raw,q=None):
 from checker import observed,cleared
 if q is None:q=json.loads((ROOT/'evidence/editable-iab.json').read_text())
 assert q['tab_closed'] and not q['console'] and list(q['cases'])==[c['id'] for c in TABLE['cases']]
 for c,a in zip(TABLE['cases'],raw['attempts']):
  r=json.loads(a['stdout']);x=q['cases'][c['id']];assert json.loads(x['result'])==r and json.loads(x['events'])==c['events'] and x['answer_open'];observed(x,c['expected']);answer_check(x,r)
 for name,pair in q['json_reset'].items():
  assert pair['before']['answer_open'];cleared(pair['after']);assert pair['after']['events']=='[{"id":1,"tick":1}]' and pair['after']['pd']==pair['before']['pd'] and pair['after']['pc']==pair['before']['pc']
 for n,pair in q['prediction_reset'].items():
  assert pair['before']['answer_open'];cleared(pair['after'])
  if n=='drop/喪失の予想':assert pair['after']['pd']=='修理後の新drop予想' and pair['after']['pc']==pair['before']['pc']
  else:assert pair['after']['pc']=='修理後の新完了予想' and pair['after']['pd']==pair['before']['pd']
def check():
 p=json.loads((ROOT/'evidence/editable-current.json').read_text());assert sha(ROOT/'evidence'/p['raw'])==p['sha256'];raw=json.loads((ROOT/'evidence'/p['raw']).read_text())
 for n,h in raw['source_sha256'].items():assert sha(ROOT/n)==h,n
 result=validate(raw);verify_ui(raw);return result
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--record',action='store_true');args=a.parse_args()
 if args.record:
  attempts=[]
  for c in TABLE['cases']:
   cmd=['python3','-B','runner.py','--case',c['case'],'--events-json',json.dumps(c['events'],separators=(',',':'))];start=utc();p=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True);attempts.append(dict(id=c['id'],command=cmd,started_utc=start,ended_utc=utc(),exit=p.returncode,stdout=p.stdout,stderr=p.stderr))
  raw=dict(utc=utc(),attempts=attempts,source_sha256={n:sha(ROOT/n) for n in ['fixture.json','oracle.json','producer.py','runner.py','server.py','index.html','ui.js','editable-oracle.json','editable.py']});name='run-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]+'.json'
  with (ROOT/'evidence'/name).open('x') as f:json.dump(raw,f,ensure_ascii=False,indent=2);f.write('\n')
  validate(raw);(ROOT/'evidence/editable-current.json').write_text(json.dumps(dict(raw=name,sha256=sha(ROOT/'evidence'/name)),indent=2)+'\n');print(name)
 else:print(json.dumps(check()))
