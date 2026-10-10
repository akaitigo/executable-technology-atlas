import json,hashlib,sys,datetime
from pathlib import Path
from fractions import Fraction
from oracle import check
from execute import SOURCES
P=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(x):return json.dumps(x,separators=(',',':'),ensure_ascii=False)
def checkraw(r,c,literal):
 assert r['source_sha256']=={n:sha(P/n) for n in SOURCES},'source mismatch'
 assert json.loads(r['input_json'])==c['input']
 assert json.loads(r['stdout'])==r['result']
 check(r['result'],c['input'],literal)
 expectedexit=3 if c.get('inject_failure') else 2 if literal and 'refused' in literal else 0
 assert r['exit']==expectedexit
 assert r['argv']==['python3','-B','model.py']+(['--fail'] if c.get('inject_failure') else [])
 assert r['stderr']=='' and r['runtime']
 assert datetime.datetime.fromisoformat(r['completed'])>=datetime.datetime.fromisoformat(r['started'])
 if expectedexit==0:
  a=r['audit'];assert a['exit']==0 and a['stderr']=='' and json.loads(a['stdout'])['status']=='AUDIT_PASSED'
  assert json.loads(a['stdin'])=={'input':c['input'],'result':r['result']};assert a['argv']==['python3','-B','oracle.py']
 else:assert r['audit'] is None

def collect():
 failures=[];checks=[]
 def run(name,f):
  try:f();checks.append(name)
  except Exception as e:failures.append(dict(check=name,reason=str(e),type=type(e).__name__))
 fixtures=json.loads((P/'fixture.json').read_text());custom=json.loads((P/'custom-oracle.json').read_text());literals=json.loads((P/'oracle.json').read_text());cases=fixtures+custom
 def literal(c):return literals.get(c['id'],c.get('literal'))
 def raw():
  ptr=json.loads((P/'evidence/current.json').read_text());file=P/'evidence'/ptr['raw'];assert sha(file)==ptr['sha256'];data=json.loads(file.read_text());assert data['status']=='passed' and not data['failures'];assert [x['id'] for x in data['attempts']]==[c['id'] for c in cases]
  for a,c in zip(data['attempts'],cases):checkraw(a['raw'],c,literal(c))
 run('raw process + independent audit + hand literal + source binding',raw)
 def contract():
  x=json.loads((P/'evidence/contract-before-producer.json').read_text());assert x['producer_absent']
  for n,b in x['files'].items():assert sha(P/n)==b['sha256'] and (P/n).stat().st_mtime_ns==b['mtime_ns']
  assert (P/'model.py').stat().st_mtime_ns>max(v['mtime_ns'] for v in x['files'].values())
 run('producer以前の契約を保持',contract)
 ui=json.loads((P/'evidence/browser.json').read_text())
 def browser():
  assert [a['id'] for a in ui['attempts']]==[c['id'] for c in cases]
  ids=set()
  for a,c in zip(ui['attempts'],cases):
   s=a['state'];packet=json.loads(s['raw']);r=packet['raw'];assert r==packet['receipt'];assert r['request_id'] not in ids;ids.add(r['request_id']);checkraw(r,c,literal(c));out=r['result'];assert s['status']==out['status'];assert a['ax']
   if out['status']!='OBSERVED':assert s['hidden'] and s['answerHidden'] and not s['shapes'];continue
   assert not s['hidden'] and not s['answerHidden'] and s['answerOpen']
   areas=[out['strategies'][k]['area'] for k in ['near_clip','no_clip','drop_outside']];assert j(areas) in s['answer']
   assert '未実証' in s['answer'] and '有限CPU' in s['answer']
   assert len(s['shapes'])==3
   for shape,(name,g) in zip(s['shapes'],out['strategies'].items()):
    assert shape['strategy']==name and json.loads(shape['polygon'])==g['polygon'] and json.loads(shape['ndc'])==g['ndc'] and shape['area']==g['area'] and json.loads(shape['fan'])==g['fan']
    coords=[tuple(map(float,z.split(','))) for z in shape['points'].split()] if shape['points'] else []
    assert len(coords)==len(g['ndc'])
    for xy,ndc in zip(coords,g['ndc']):assert abs(xy[0]-(180+140*float(Fraction(ndc[0]))))<1e-8 and abs(xy[1]-(200-140*float(Fraction(ndc[1]))))<1e-8
   expectedrows=[[name,j(g['polygon']),j(g['ndc']),j(g['fan'])+' / '+j(g['fan_signed_areas']),g['signed_area']+' / '+g['area']+' / '+g['state']] for name,g in out['strategies'].items()]
   assert s['geometry'][1:]==expectedrows
   assert s['intersections'][1:]==[[j(x['edge']),x['t'],j(x['point'])] for x in out['intersections']]
 run('19 UI: raw/receipt + SVG点 + 表 + 答え',browser)
 def controls():
  d={x['id']:x['state'] for x in ui['controls']};assert d['answer-before-reset']['answerOpen']
  for n in ['prediction-clears','json-clears','case-clears','reset-clears','stale-ignored']:
   x=d[n];assert x['status']=='未実行' and x['hidden'] and x['answerHidden'] and not x['answerOpen'] and not x['shapes'] and x['raw']==''
  assert d['held']['status']=='実行済み・結果保留' and d['held']['hidden'];assert d['stale-ignored']['ignored']=='古い結果の無視: 1';assert d['http503']['status']=='COMMUNICATION_FAILURE' and json.loads(d['http503']['raw'])=={'reason':'HTTP 503'}
 run('入力失効 / 保留 / 古い結果 / 503',controls)
 def docs():
  for d in ui['documents']:
   if 'file' in d:
    n=d['file'];file=P/n;assert sha(file)==d['sha256'] and len(file.read_text())==d['length']
  d={x.get('primary'):x for x in ui['documents'] if 'primary' in x};assert d['clip-condition']['w_positive_present'] and d['clip-condition']['near_far_present'];assert all(d['rasterizer-wording-check']['proof'].values())
 run('実文書viewer + 公式本文リンク',docs)
 def negative():
  from test_negative import collect as neg
  r=neg();assert r['status']=='passed' and r['mutants']==23 and len(r['schema'])==8
 run('23 mutants / 8 schema refusal actual probes',negative)
 return dict(status='failed' if failures else 'passed',checks=checks,failures=failures,completed=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=len(cases),browser_cases=len(ui['attempts']),negative_mutants=23,schema_refusals=8,source_sha256={n:sha(P/n) for n in SOURCES})
if __name__=='__main__':
 if sys.argv[1:] not in [[],['--record']]:print(json.dumps(dict(status='INPUT_REFUSED',reason='ARGUMENT')));sys.exit(2)
 r=collect()
 if sys.argv[1:]:
  name='verification-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json';(P/'evidence'/name).write_text(json.dumps(r,indent=2)+'\n')
  if r['status']=='passed':(P/'evidence/verification.json').write_text(json.dumps(r,indent=2)+'\n')
 print(json.dumps(r));sys.exit(0 if r['status']=='passed' else 1)
