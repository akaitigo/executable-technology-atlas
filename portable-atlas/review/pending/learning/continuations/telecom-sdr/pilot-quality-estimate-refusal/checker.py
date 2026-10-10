import json,hashlib,sys,datetime,copy
from pathlib import Path
from fractions import Fraction as F
from oracle import check,compare
from execute import SOURCES
P=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(x):return json.dumps(x,separators=(',',':'),ensure_ascii=False)
def text(x):return 'null' if x is None else str(x)
def rawcheck(r,c,literal=None):
 assert r['source_sha256']=={n:sha(P/n) for n in SOURCES},'source binding'
 inp=json.loads(r['input_json']);assert inp==c['input'];assert set(inp)=={'known_pilot','pilot_rx','payload_rx','min_gain_sq','max_residual'},'truth leaked'
 assert json.loads(r['stdout'])==r['result'];check(r['result'],inp,literal,c['truth'])
 assert r['exit']==(3 if c.get('inject_failure') else 0);assert r['stderr']==''
 assert r['argv']==['python3','-B','model.py']+(['--fail'] if c.get('inject_failure') else [])
 assert datetime.datetime.fromisoformat(r['completed'])>=datetime.datetime.fromisoformat(r['started'])
 if r['exit']==0:
  a=r['audit'];assert a['exit']==0 and a['stderr']=='' and json.loads(a['stdout'])['status']=='AUDIT_PASSED';assert json.loads(a['stdin'])=={'input':inp,'result':r['result']};assert a['argv']==['python3','-B','oracle.py']
 else:assert r['audit'] is None
 if 'harness' in r:assert r['harness']==compare(r['result'],c['truth'])

def uicheck(a,c,literal=None):
 s=a['state'];packet=json.loads(s['raw']);r=packet['raw'];assert r==packet['receipt'];rawcheck(r,c,literal);assert a['ax'];assert s['status']==r['result']['status']
 if s['status']!='OBSERVED':assert s['hidden'] and s['answerHidden'] and not s['points'];return
 out=r['result'];h=r['harness'];assert h==compare(out,c['truth']);assert s['answerOpen'] and not s['answerHidden'] and not s['hidden']
 assert '期待拒否は成功受信に含めない' in s['answer'] and '未実証' in s['answer'] and j(h['policies']['gated']) in s['answer'] and j(h['policies']['naive']) in s['answer']
 st=out['stats'];assert s['stats']=='h='+j(st['h'])+' / |h|²='+text(st['h2'])+' / Ek='+st['known_energy']+' / Er='+st['rx_energy']+' / SSE='+text(st['sse'])+' / NR='+text(st['normalized_residual'])
 assert s['gates'][1:]==[['magnitude²','>= '+out['gates']['min_gain_sq'],str(st['h2']) if st['h2'] is not None else 'null',j(out['gates']['magnitude_pass'])],['normalized residual','<= '+out['gates']['max_residual'],str(st['normalized_residual']) if st['normalized_residual'] is not None else 'null',j(out['gates']['residual_pass'])]]
 rows=[[str(x['index']),j(x['known']),j(x['rx']),j(x['correlation']),x['known_energy']+' / '+x['rx_energy'],j(x['fit']),j(x['residual']),str(x['residual_energy']) if x['residual_energy'] is not None else 'null'] for x in out['rows']];assert s['pilot'][1:]==rows
 rows=[]
 for name,p in out['policies'].items():
  q=h['policies'][name];rows.append([name,p['status']+' / '+j(p['reasons']),j(p['factor']),j(p['corrected']),j(p['decisions']),j(h['truth']),j(q['error_positions']),str(q['compared_bits'])+' / '+text(q['ber'])+' / '+q['verdict']])
 assert s['payload'][1:]==rows
 panels=[('pilot rx',out['input']['pilot_rx']),('payload rx',out['input']['payload_rx']),('gated corrected',out['policies']['gated']['corrected']),('naive corrected',out['policies']['naive']['corrected'])];expected=[]
 for name,points in panels:
  if points is None:continue
  scale=max([1]+[abs(float(F(c))) for p in points for c in p])
  for i,p in enumerate(points):expected.append((name,i,p,scale))
 assert len(s['points'])==len(expected)
 for v,(panel,i,p,scale) in zip(s['points'],expected):
  assert v['panel']==panel and int(v['index'])==i and json.loads(v['iq'])==p and float(v['scale'])==scale
  assert abs(float(v['cx'])-(135+100*float(F(p[0]))/scale))<1e-8 and abs(float(v['cy'])-(190-100*float(F(p[1]))/scale))<1e-8

def collect():
 checks=[];fails=[]
 def run(n,f):
  try:f();checks.append(n)
  except Exception as e:fails.append(dict(check=n,reason=str(e),type=type(e).__name__))
 fix=json.loads((P/'fixture.json').read_text());custom=json.loads((P/'custom-oracle.json').read_text());cases=fix+custom;literal=json.loads((P/'oracle.json').read_text());ptr=json.loads((P/'evidence/current.json').read_text());rawpath=P/'evidence'/ptr['raw'];data=json.loads(rawpath.read_text());ui=json.loads((P/'evidence/browser.json').read_text());lit=lambda c:literal.get(c['id'],c.get('literal'))
 def cli():
  assert sha(rawpath)==ptr['sha256'] and data['status']=='passed' and not data['failures'];assert [x['id'] for x in data['attempts']]==[c['id'] for c in cases]
  for a,c in zip(data['attempts'],cases):rawcheck(a['raw'],c,lit(c));assert a['harness']==compare(a['raw']['result'],c['truth'])
 run('22 actual receiver processes / independent audits / hand arithmetic / harness',cli)
 def contract():
  x=json.loads((P/'evidence/contract-before-producer.json').read_text());assert x['producer_absent']
  for n,b in x['files'].items():assert sha(P/n)==b['sha256'] and (P/n).stat().st_mtime_ns==b['mtime_ns']
  assert (P/'model.py').stat().st_mtime_ns>max(b['mtime_ns'] for b in x['files'].values())
 run('producer以前の手契約保持',contract)
 def browser():
  assert [a['id'] for a in ui['attempts']]==[c['id'] for c in cases]
  for a,c in zip(ui['attempts'],cases):uicheck(a,c,lit(c))
 run('22 UI: I/Q points / arithmetic rows / gate / refused payload / answer / receipt',browser)
 def operations():
  assert [a['id'] for a in ui['operations']]==['scale-only','noise-only','residual-threshold-only','magnitude-threshold-only']
  wanted=[custom[0],fix[7],custom[1],copy.deepcopy(fix[0])];wanted[3]['input']['min_gain_sq']='2'
  for a,c in zip(ui['operations'],wanted):uicheck(a,c)
  st=[json.loads(a['state']['raw'])['raw']['result']['stats'] for a in ui['operations']];assert st[0]['h2']=='1/4' and st[0]['normalized_residual']=='1/2';assert st[1]['h']==['1','0'] and st[1]['normalized_residual']=='1/2';assert st[2]==st[1];assert st[3]['h2']=='1' and st[3]['normalized_residual']=='0'
  controls=[json.loads(a['state']['raw'])['raw']['construction']['controls'] for a in ui['operations']];assert controls[0]['scale']=='1/2' and controls[0]['noise']=='';assert controls[1]['noise']=='1' and controls[1]['scale']=='';assert controls[2]['max_residual']=='1/4' and controls[3]['min_gain_sq']=='2'
 run('magnitude / residual / 2閾値の独立実操作',operations)
 def control():
  d={a['id']:a['state'] for a in ui['controls']}
  for n in ['prediction-clears','scale-clears','noise-clears','minimum-clears','maximum-clears','json-clears','case-clears','reset-clears','stale-ignored']:
   x=d[n];assert x['status']=='未実行' and x['hidden'] and x['answerHidden'] and not x['answerOpen'] and not x['points'] and x['raw']==''
  assert d['held']['status']=='実行済み・結果保留' and d['held']['hidden'];assert int(d['stale-ignored']['ignored'].split(': ')[1])==int(d['held']['ignored'].split(': ')[1])+1
  assert d['http503']['status']=='COMMUNICATION_FAILURE' and json.loads(d['http503']['raw'])=={'reason':'HTTP 503'};x=d['invalid-json'];assert x['status']=='INPUT_REFUSED' and x['hidden'] and x['answerHidden'];r=json.loads(x['raw'])['raw'];assert r['exit']==2 and r['audit'] is None and r['harness']['successful_receptions']==0
 run('全編集 / reset / 古い応答 / 503 / 不正JSON',control)
 def docs():
  for d in ui['documents']:
   if 'file' in d:assert sha(P/d['file'])==d['sha256'] and len((P/d['file']).read_text())==d['length']
  d=next(x for x in ui['documents'] if x.get('primary')=='MIT6.450-Ch8-HTML');assert d['chapter_heading'] and d['detection_description'] and d['download_href'].endswith('book_8.pdf')
  assert json.loads((P/'evidence/pdf-display-limit.json').read_text())['status']=='UNOBSERVED_PDF_BODY_IN_IAB'
 run('13 viewer本文 + MIT HTML入口 + PDF表示限界保持',docs)
 def negatives():
  from test_negative import collect as neg
  x=neg();assert x['status']=='passed' and x['mutants']==25 and len(x['harness_mutants'])==5 and len(x['schema'])==9
 run('25 receiver / 5 harness mutations + 9 actual schema refusals',negatives)
 summary={k:{'ACCEPTED_CORRECT':0,'ACCEPTED_ERROR':0,'REFUSED':0,'EXECUTION_FAILED':0} for k in ['gated','naive']}
 for a in data['attempts']:
  if a['raw']['result']['status']=='EXECUTION_FAILED':
   for k in summary:summary[k]['EXECUTION_FAILED']+=1
  else:
   for k in summary:summary[k][a['harness']['policies'][k]['verdict']]+=1
 return dict(status='failed' if fails else 'passed',checks=checks,failures=fails,completed=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=22,browser_cases=22,independent_operations=4,summary=summary,source_sha256={n:sha(P/n) for n in SOURCES})
if __name__=='__main__':
 if sys.argv[1:] not in [[],['--record']]:print(json.dumps(dict(status='INPUT_REFUSED',reason='ARGUMENT')));sys.exit(2)
 x=collect()
 if sys.argv[1:]:
  name='verification-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json';(P/'evidence'/name).write_text(json.dumps(x,indent=2)+'\n')
  if x['status']=='passed':(P/'evidence/verification.json').write_text(json.dumps(x,indent=2)+'\n')
 print(json.dumps(x));sys.exit(0 if x['status']=='passed' else 1)
