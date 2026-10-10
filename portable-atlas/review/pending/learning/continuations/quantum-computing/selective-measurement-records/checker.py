import json,hashlib,sys,datetime,copy
from pathlib import Path
from fractions import Fraction as F
from oracle import check
from execute import SOURCES
P=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def j(x):return json.dumps(x,separators=(',',':'),ensure_ascii=False)
def rawcheck(r,c,literal=None):
 assert r['source_sha256']=={n:sha(P/n) for n in SOURCES},'source mismatch'
 assert json.loads(r['input_json'])==c['input'];assert json.loads(r['stdout'])==r['result'];check(r['result'],c['input'],literal)
 assert r['exit']==(3 if c.get('inject_failure') else 0) and r['stderr']==''
 assert r['argv']==['python3','-B','model.py']+(['--fail'] if c.get('inject_failure') else [])
 assert datetime.datetime.fromisoformat(r['completed'])>=datetime.datetime.fromisoformat(r['started'])
 if r['exit']==0:
  a=r['audit'];assert a['exit']==0 and a['stderr']=='' and json.loads(a['stdout'])['status']=='AUDIT_PASSED';assert json.loads(a['stdin'])=={'input':c['input'],'result':r['result']};assert a['argv']==['python3','-B','oracle.py']
 else:assert r['audit'] is None

def uicheck(a,c,literal=None):
 s=a['state'];pack=json.loads(s['raw']);r=pack['raw'];assert r==pack['receipt'];rawcheck(r,c,literal);assert a['ax'];assert s['status']==r['result']['status']
 if s['status']!='OBSERVED':assert s['hidden'] and s['answerHidden'] and not s['panels'];return
 out=r['result'];assert not s['hidden'] and not s['answerHidden'] and s['answerOpen'];assert json.loads(s['selection'])==out['selection']
 assert j(out['discard']['h_of_weighted']['density']) in s['answer'];assert '正しいweighted ensembleとequal-weight故障のH後Z確率一致=' in s['answer'];assert '正規化漏れは別: H後Z='+j(out['faults']['omit_normalization']['after_h']['z_probabilities']) in s['answer'];assert '未実証' in s['answer'] and '説明用指定' in s['answer']
 rows=[]
 for b in out['branches']:rows.append([str(b['outcome']),j(b['sigma']['density'])+' / '+b['sigma']['trace'],b['p'],b['status'],j(b['conditional']['density'])+' / '+b['conditional']['trace'] if b['conditional'] else 'null',j(b['after_h']['density'])+' / '+j(b['after_h']['z_probabilities']) if b['after_h'] else 'null'])
 assert s['branches'][1:]==rows
 rows=[]
 for key in ['weighted','direct','h_of_weighted','h_of_direct','weighted_after_h']:
  g=out['discard'][key];rows.append([key,j(g['density']),g['trace'],j(g['z_probabilities'])])
 assert s['discard'][1:]==rows
 rows=[[key,j(out['faults'][key]),'全density一致='+str(out['faults'][key]['full_equal']).lower()] for key in ['omit_normalization','equal_weights']];rows.append(['zero_division',j(out['faults']['zero_division']),'正常branchのpk0は割らない']);assert s['faults'][1:]==rows
 panels=[('σ0 / trace='+out['branches'][0]['p'],out['branches'][0]['sigma']),('conditional0',out['branches'][0]['conditional']),('conditional1',out['branches'][1]['conditional']),('weighted H後',out['discard']['h_of_weighted']),('等重み故障 H後',out['faults']['equal_weights']['after_h']),('正規化漏れ H後',out['faults']['omit_normalization']['after_h'])];wanted=[(label,g) for label,g in panels if g is not None];assert len(s['panels'])==len(wanted)
 for v,(label,g) in zip(s['panels'],wanted):
  assert v['panel']==label and json.loads(v['density'])==g['density'] and v['trace']==g['trace'];text=label+''.join(z[0]+' + i·'+z[1] for row in g['density'] for z in row)+'trace='+g['trace']+' / Z='+j(g['z_probabilities']);assert v['text']==text

def collect():
 checks=[];fails=[]
 def run(n,f):
  try:f();checks.append(n)
  except Exception as e:fails.append(dict(check=n,reason=str(e),type=type(e).__name__))
 fix=json.loads((P/'fixture.json').read_text());custom=json.loads((P/'custom-oracle.json').read_text());cases=fix+custom;lit=json.loads((P/'oracle.json').read_text());literal=lambda c:lit.get(c['id'],c.get('literal'));ptr=json.loads((P/'evidence/current.json').read_text());file=P/'evidence'/ptr['raw'];data=json.loads(file.read_text());ui=json.loads((P/'evidence/browser.json').read_text())
 def raw():
  assert sha(file)==ptr['sha256'] and data['status']=='passed' and not data['failures'];assert [a['id'] for a in data['attempts']]==[c['id'] for c in cases]
  for a,c in zip(data['attempts'],cases):rawcheck(a['raw'],c,literal(c))
 run('17実process / 別audit / σ-p-conditional / 手literal / 全density',raw)
 def contract():
  x=json.loads((P/'evidence/contract-before-producer.json').read_text());assert x['producer_absent']
  for n,b in x['files'].items():assert sha(P/n)==b['sha256'] and (P/n).stat().st_mtime_ns==b['mtime_ns']
  assert (P/'model.py').stat().st_mtime_ns>max(b['mtime_ns'] for b in x['files'].values())
 run('先固定契約とoracle保持',contract)
 def browser():
  assert [a['id'] for a in ui['attempts']]==[c['id'] for c in cases]
  for a,c in zip(ui['attempts'],cases):uicheck(a,c,literal(c))
 run('17 UI raw/receipt / matrix diagram全成分 / 全表 / 答え',browser)
 def operations():
  assert [a['id'] for a in ui['operations']]==['record-0','record-1','record-discard']
  for a,r in zip(ui['operations'],[0,1,'discard']):
   c=copy.deepcopy(fix[5]);c['input']['record']=r;uicheck(a,c)
 run('record保持0/1/破棄の独立操作',operations)
 def controls():
  d={a['id']:a['state'] for a in ui['controls']}
  for n in ['prediction-clears','record-clears','json-clears','case-clears','reset-clears','stale-ignored']:
   s=d[n];assert s['status']=='未実行' and s['hidden'] and s['answerHidden'] and not s['answerOpen'] and not s['panels'] and s['raw']==''
  assert d['held']['status']=='実行済み・結果保留';assert int(d['stale-ignored']['ignored'].split(': ')[1])==int(d['held']['ignored'].split(': ')[1])+1
  assert d['http503']['status']=='COMMUNICATION_FAILURE' and json.loads(d['http503']['raw'])=={'reason':'HTTP 503'};x=d['invalid-density'];assert x['status']=='INPUT_REFUSED' and x['hidden'] and x['answerHidden'];r=json.loads(x['raw'])['raw'];assert r['exit']==2 and r['audit'] is None and r['result']['reason']=='DENSITY'
 run('3編集 / case/reset / 旧保留 / 503 / 不正density',controls)
 def docs():
  assert len([d for d in ui['documents'] if 'file' in d])==12
  for d in ui['documents']:
   if 'file' in d:assert sha(P/d['file'])==d['sha256'] and len((P/d['file']).read_text())==d['length']
   else:assert d['locator_present'] and d['url'].startswith('https://quantum.cloud.ibm.com/')
 run('12文書viewer本文 / 3 IBM公式本文locator',docs)
 def negative():
  from test_negative import collect as neg
  x=neg();assert x['status']=='passed' and x['mutants']==23 and len(x['schema'])==10 and x['probability_only_blind_spot']
 run('23 mutants / 10 schema subprocess / 確率だけの故障見逃し',negative)
 return dict(status='failed' if fails else 'passed',checks=checks,failures=fails,completed=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=17,browser_cases=17,record_operations=3,source_sha256={n:sha(P/n) for n in SOURCES})
if __name__=='__main__':
 if sys.argv[1:] not in [[],['--record']]:print(json.dumps(dict(status='INPUT_REFUSED',reason='ARGUMENT')));sys.exit(2)
 x=collect()
 if sys.argv[1:]:
  name='verification-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json';(P/'evidence'/name).write_text(json.dumps(x,indent=2)+'\n')
  if x['status']=='passed':(P/'evidence/verification.json').write_text(json.dumps(x,indent=2)+'\n')
 print(json.dumps(x));sys.exit(0 if x['status']=='passed' else 1)
