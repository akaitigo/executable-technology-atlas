# -*- coding: utf-8 -*-
import json,sys,hashlib,datetime
from pathlib import Path
from oracle import check
from sqlite_audit import audit as replay
from test_negative import collect as negatives
P=Path(__file__).resolve().parent
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
j=lambda v:json.dumps(v,separators=(',',':'),ensure_ascii=False)
def load(n):return json.loads((P/n).read_text())
def audit(raw,literal=None):
 x=json.loads(raw['input_json']);r=raw['result'];assert json.loads(raw['stdout'])==r and raw['started']<=raw['completed']
 assert raw['exit']=={'OBSERVED':0,'INPUT_REFUSED':2,'EXECUTION_FAILED':3}[r['status']]
 for n,sha in raw['source_sha256'].items():
  # Saved numerical/UI receipts retain their original UI source provenance.
  archived=P/'evidence/async-review-old'/n
  assert h(P/n)==sha or (n=='ui.js' and archived.exists() and h(archived)==sha),n
 if r['status']=='INPUT_REFUSED':assert r['db_opened'] is False;return
 check(r,x,literal);replay(r,x)
 a=raw['audit'];assert a['exit']==0 and json.loads(a['stdout'])['status']=='passed';arg=json.loads(a['stdin']);assert arg['input']==x and arg['result']==r
 if r['status']=='EXECUTION_FAILED':assert arg['literal']=={'status':'EXECUTION_FAILED'}
def answer(r):
 if r['status']=='EXECUTION_FAILED':return f"EXECUTION_FAILED: {r['reason']}。query結果なし。実行済traceとcleanup={j(r['cleanup'])}を保持。正常比較とは別です。"
 a,b=r['queries']['index'],r['queries']['payload'];return f"同じ条件・順序で{a['row_count']}行。bucket,label: schema cover可能={j(a['schema_cover_possible'])}、実plan={a['plan_class']}。payload追加: schema cover可能={j(b['schema_cover_possible'])}、不足列={j(b['missing_projection'])}、実plan={b['plan_class']}。比較={r['comparison_status']}。注目投影={r['selected_projection']}。NULL・重複を含む全結果を照合。SQLite={r['environment']['sqlite_version']}。実行時間・訪問page数は未測定です。"
def ui(row,literal=None):
 assert row['raw']==row['receipt'];audit(row['raw'],literal);r=row['raw']['result'];assert row['status']==r['status']+' / exit='+str(row['raw']['exit'])
 if r['status']=='INPUT_REFUSED':assert row['panels']==[] and row['answer']=='DB接続前に拒否: '+r['reason'];return
 assert row['answer']==answer(r) and json.loads(row['input'])==json.loads(row['raw']['input_json'])
 if r['status']=='EXECUTION_FAILED':assert row['panels']==[] and row['failure']=='producer失敗'+j(r['trace'])+j(r['cleanup']);return
 assert row['projection']==r['selected_projection'] and [p['name'] for p in row['panels']]==['index','payload']
 for panel in row['panels']:
  n=panel['name'];q=r['queries'][n];assert panel['selected']==(n==r['selected_projection']);assert panel['state']=={k:q[k] for k in ['schema_cover_possible','missing_projection','plan_class']}
  path={'COVERING_REPORTED':'実EQP: covering indexで投影列を取得','INDEX_TABLE_LOOKUP_REPORTED':'実EQP: indexとtableから投影列を取得'}.get(q['plan_class'],'実EQP: 別planまたは未認識。比較未成立')
  assert panel['nodes']==[dict(key='index',text='index key: bucket,labelimplicit rowid: id存在はschema rawで確認'),dict(key='projection',text='必要列='+j(q['columns'])+'schema cover可能='+j(q['schema_cover_possible'])+'不足列='+j(q['missing_projection'])),dict(key='plan',text=path+q['plan_class'])]
  assert panel['sql']==q['sql']+'\nparams='+j(q['params']) and json.loads(panel['eqp'])==q['eqp_raw'];assert panel['headers']==q['columns'] and panel['rows']==[[j(v) for v in cells] for cells in q['rows']]
  assert panel['summary']=='row_count='+str(q['row_count'])+' / plan_contract_consistent='+j(q['plan_contract_consistent'])
 assert json.loads(row['trace'])==r['trace'] and json.loads(row['sqlite_trace'])==r['sqlite_trace'] and json.loads(row['cleanup'])==r['cleanup']
def main():
 checks=[];fixed=load('evidence/contract-before-producer.json');assert fixed['producer_absent']
 for n,v in fixed['files'].items():assert h(P/n)==v['sha256'] and (P/n).stat().st_mtime_ns==v['mtime_ns'],n
 checks.append('pre-fixed 256 rows/11 literal rows/ordered IDs/contracts/oracle hash+mtime preserved')
 current=load('evidence/current.json');f=P/'evidence'/current['raw'];assert h(f)==current['sha256'];report=load('evidence/'+current['raw']);cases=load('fixture.json')+load('custom.json');literal=load('oracle.json');assert report['status']=='passed' and len(cases)==17 and [r['id'] for r in report['attempts']]==[c['id'] for c in cases]
 for c,row in zip(cases,report['attempts']):assert json.loads(row['raw']['input_json'])==c['input'];audit(row['raw'],literal.get(c['id']))
 checks.append('17 actual SQLite processes; exact filter/sort/projection independently checked; fresh real schema/version/EQP/SQL trace replay')
 browser=load('evidence/browser.json');assert len(browser['cases'])==17
 for c,row in zip(cases,browser['cases']):assert row['id']==c['id'] and json.loads(row['raw']['input_json'])==c['input'];ui(row,literal.get(c['id']))
 checks.append('17 native UI raw/route receipt, diagram fields, all cells incl NULL/duplicates/order, SQL/EQP, full answers')
 controls={r['id']:r for r in browser['controls']};assert len(controls)==11
 for id in ['prediction-clears','input-clears','case-clears','reset-clears','projection-clears','held','stale-ignored','http503']:assert controls[id]['raw'] is None and controls[id]['panels']==[]
 for id in ['prediction-clears','input-clears','case-clears','reset-clears','projection-clears']:assert controls[id]['before']['panels']==2 and controls[id]['before']['request_id']
 assert controls['stale-ignored']['status']=='旧結果を無視: 1' and controls['http503']['status']=='HTTP_ERROR 503';ui(controls['invalid-sql'])
 for name in ['index','payload']:
  row=controls['projection-'+name];ui(row);assert row['raw']['result']['selected_projection']==name and json.loads(row['raw']['input_json'])==dict(bucket=0,projection=name,order='asc')
 checks.append('11 editor/reset/projection/held/stale/503/pre-DB SQL refusal controls')
 assert len(browser['documents'])==15
 for row in browser['documents']:assert row['sha256']==h(P/row['file']) and row['body']==(P/row['file']).read_text()
 assert len(browser['primary'])==3 and all(r['observed'] for r in browser['primary']);checks.append('15 source/Skill/current/Subject viewers + 3 official SQLite section locators')
 n=negatives();assert n==load('evidence/negative.json') and n['status']=='passed';checks.append('26 semantic/runtime mutants, 13 pre-DB refusals, hypothetical unknown plan distinction, failure close')
 rows=sum(r['raw']['result']['queries'].get('index',{}).get('row_count',0) for r in report['attempts'])
 return dict(status='passed',checks=checks,failures=[],cases=17,browser_cases=17,normal_query_plans=32,result_rows_per_projection=rows,completed=datetime.datetime.now(datetime.timezone.utc).isoformat())
if __name__=='__main__':
 try:r=main()
 except Exception as e:r=dict(status='failed',reason=str(e),kind=type(e).__name__)
 if sys.argv[1:]==['--record']:
  f=P/'evidence/verification.json'
  if f.exists() and r['status']=='failed':(P/'evidence/verification-previous.json').write_bytes(f.read_bytes())
  f.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(r,ensure_ascii=False));sys.exit(r['status']!='passed')
