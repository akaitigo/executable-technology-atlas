import json,sys,hashlib,datetime,subprocess
from pathlib import Path
from oracle import check
from test_negative import collect as negatives
P=Path(__file__).resolve().parent
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
j=lambda x:json.dumps(x,separators=(',',':'),ensure_ascii=False)
def load(n):return json.loads((P/n).read_text())
def audit(raw,literal=None):
 x=json.loads(raw['input_json']);r=raw['result'];assert json.loads(raw['stdout'])==r
 assert raw['runtime'];assert raw['started']<=raw['completed']
 assert raw['exit']==({'OBSERVED':0,'INPUT_REFUSED':2,'EXECUTION_FAILED':3}[r['status']])
 for n,sha in raw['source_sha256'].items():assert h(P/n)==sha,n
 if r['status']=='OBSERVED':
  check(r,x,literal);a=raw['audit'];assert a['exit']==0 and json.loads(a['stdout'])['status']=='passed';arg=json.loads(a['stdin']);assert arg==dict(input=x,result=r)
 elif literal:check(r,x,literal)
def main():
 checks=[];frozen=load('evidence/contract-before-producer.json');assert frozen['producer_absent']
 for n,v in frozen['files'].items():assert h(P/n)==v['sha256'] and (P/n).stat().st_mtime_ns==v['mtime_ns'],n
 checks.append('pre-fixed contract/oracle preserved')
 current=load('evidence/current.json');assert h(P/'evidence'/current['raw'])==current['sha256'];raw=load('evidence/'+current['raw']);assert raw['status']=='passed'
 cases=load('fixture.json')+load('custom.json');literal=load('oracle.json');assert [a['id'] for a in raw['attempts']]==[c['id'] for c in cases]
 for c,a in zip(cases,raw['attempts']):assert json.loads(a['raw']['input_json'])==c['input'];audit(a['raw'],literal.get(c['id']))
 base=raw['attempts'][0]['raw']['result'];hand=load('hand-trace.json')
 for pol,rows in hand.items():
  observed=[[r['event'],r['local_sets']['A'],r['local_sets']['B'],r['latest_responses'],r['delivered_set']['A'],r['delivered_set']['B'],r['global_business_ok']] for r in base['policies'][pol]['trace']];assert observed==rows
 checks.append('16 producer processes / independent audit / complete trace / handwritten table')
 schedule=load('evidence/schedules.json');assert schedule['status']=='passed' and schedule['positional']==26 and schedule['unique']==8 and sum(r['multiplicity'] for r in schedule['runs'])==26
 assert len({tuple(r['schedule']) for r in schedule['runs']})==8
 for r in schedule['runs']:
  audit(r['raw']);assert json.loads(r['raw']['input_json'])['schedule']==r['schedule']
  for pol,v in r['raw']['result']['policies'].items():
   f=v['final'];assert f['converged'] and f['global_business_ok']==(pol=='deferred');assert sum(f['delivery_count'].values())==len(r['schedule']);assert f['delivered_set']=={'A':['B>A'],'B':['A>B']}
 checks.append('8 unique schedules actually executed; 26 positional multiplicities')
 browser=load('evidence/browser.json');assert len(browser['cases'])==16
 for c,row in zip(cases,browser['cases']):
  assert row['id']==c['id'];assert row['raw']==row['receipt'];assert json.loads(row['raw']['input_json'])==c['input'];audit(row['raw'],literal.get(c['id']))
  r=row['raw']['result'];assert row['status']==r['status']+' / exit='+str(row['raw']['exit'])
  if r['status']!='OBSERVED':assert not row['panels'] and r['status'] in row['answer'];continue
  assert len(row['panels'])==2
  for panel in row['panels']:
   v=r['policies'][panel['policy']];f=v['final'];assert panel['state']==f
   assert panel['chips']==[j(f['local_sets'][n]) for n in ('A','B')]
   assert json.loads(panel['responses'])==f['response_history']
   assert panel['summary']==('accepted_returned='+j(f['accepted_returned'])+'pending='+j(f['pending_ids'])+'converged='+str(f['converged']).lower()+' / global_business_ok='+str(f['global_business_ok']).lower()+'replica_bounds='+j(f['replica_bounds'])+'all_messages_delivered='+str(v['all_messages_delivered']).lower())
   want=[]
   for tr in v['trace']:
    want.append([tr['event']+'\n'+str(tr['link_up']).lower(),j(tr['local_decision'])+'\n'+j(tr['response_event']),j(tr['local_sets']['A'])+'\n'+j(tr['local_sets']['B']),j(tr['accepted_returned'])+'\n'+j(tr['pending_ids']),j(tr['delivered_set'])+'\n'+j(tr['delivery_count']),str(tr['converged']).lower()+'\n'+str(tr['global_business_ok']).lower()])
   assert panel['rows']==want,(row['id'],panel['policy'])
  o=r['policies']['optimistic']['final'];d=r['policies']['deferred']['final'];answer=f"即時受理: accepted {len(o['accepted_returned'])}件 / 上限{c['input']['capacity']} / 一致={str(o['converged']).lower()} / 業務上限={str(o['global_business_ok']).lower()}。保留: 初回pending {len(c['input']['requests'])}件からaccepted {len(d['accepted_returned'])}件・rejected {sum(s=='rejected' for s in d['latest_responses'].values())}件へ判定 / 一致={str(d['converged']).lower()} / 業務上限={str(d['global_business_ok']).lower()}。復旧は配送ではなく、集合の一致とaccepted上限は別に検査します。"
  assert row['answer']==answer
 checks.append('16 native UI raw/receipt, diagram cells, all trace table cells, answers')
 controls={c['id']:c for c in browser['controls']};assert len(controls)==8
 for n in ['prediction-clears','input-clears','case-clears','reset-clears','held','stale-ignored','http503']:
  row=controls[n];assert row['raw'] is None and row['panels']==[]
 assert controls['stale-ignored']['status']=='旧結果を無視: 1';assert controls['http503']['status']=='HTTP_ERROR 503';row=controls['invalid-capacity'];assert row['raw']==row['receipt'];audit(row['raw']);assert row['raw']['exit']==2 and row['panels']==[]
 checks.append('8 editor/reset/held/stale/503/refusal controls')
 docs=browser['documents'];assert len(docs)>=13
 for row in docs:
  f=(P/row['file']).resolve();assert row['sha256']==h(f) and row['body']==f.read_text(),row['file']
 checks.append('13 document viewers matched actual file bytes')
 n=negatives();assert n==load('evidence/negative.json') and n['status']=='passed';checks.append('21 output mutants / 12 real schema refusal processes')
 return dict(status='passed',checks=checks,failures=[],completed=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=16,browser_cases=16,schedule_unique=8,schedule_positional=26)
if __name__=='__main__':
 try:r=main()
 except Exception as e:r=dict(status='failed',reason=str(e),kind=type(e).__name__)
 if sys.argv[1:]==['--record']:(P/'evidence/verification.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(r,ensure_ascii=False));sys.exit(r['status']!='passed')
