import json,sys,hashlib,datetime
from pathlib import Path
from oracle import check
from syscall_audit import audit as syscall_audit
from test_negative import collect as negatives
P=Path(__file__).resolve().parent
h=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
j=lambda x:json.dumps(x,separators=(',',':'),ensure_ascii=False)
def load(n):return json.loads((P/n).read_text())
def audit(raw,literal=None):
 x=json.loads(raw['input_json']);r=raw['result'];assert json.loads(raw['stdout'])==r and raw['started']<=raw['completed']
 assert raw['exit']=={'OBSERVED':0,'INPUT_REFUSED':2,'EXECUTION_FAILED':3,'OS_EXCEPTION_OBSERVED':4,'OS_EXCEPTION_UNEXPECTED':5}[r['status']]
 for n,sha in raw['source_sha256'].items():
  archived=P/'evidence/wrap-review-old'/n
  assert h(P/n)==sha or (n=='index.html' and archived.exists() and h(archived)==sha),n
 if r['status']=='INPUT_REFUSED':assert r['mutation_started'] is False;return
 check(r,x,literal);syscall_audit(r,x)
 a=raw['audit'];assert a['exit']==0 and json.loads(a['stdout'])['status']=='passed';arg=json.loads(a['stdin']);assert arg['input']==x and arg['result']==r
 if r['status']=='EXECUTION_FAILED':assert arg['literal']=={'status':'EXECUTION_FAILED'}
def answer(r):
 if r['status']=='OBSERVED':
  a,b,c=r['runs'];return f"unlink後: 旧FD={j(a['trace'][-1]['old_fd']['bytes'])}、新open={a['trace'][-1]['pathname']['status']}。単一replace後: 旧FD={j(b['trace'][-1]['old_fd']['bytes'])}、新open={j(b['trace'][-1]['pathname']['bytes'])}。多step gap: 新open={c['trace'][1]['pathname']['status']}、同期callback {c['gap_callback_count']}回。fsync={'RETURNED' if r['input_echo']['fsync'] else 'SKIPPED'}、crash durability={r['durability']}。pathname更新と既存FDの参照は別です。"
 return f"{r['status']}: {j(r['runs'][0]['exception'])}。部分traceとcleanup={j(r['cleanup'])}を保持。正常比較・gap・OS例外・producer失敗は別の結果です。"
def main():
 checks=[];fixed=load('evidence/contract-before-producer.json');assert fixed['producer_absent']
 for n,v in fixed['files'].items():assert h(P/n)==v['sha256'] and (P/n).stat().st_mtime_ns==v['mtime_ns'],n
 checks.append('pre-fixed contract/hand table/oracle preserved')
 current=load('evidence/current.json');assert h(P/'evidence'/current['raw'])==current['sha256'];report=load('evidence/'+current['raw']);assert report['status']=='passed';cases=load('fixture.json')+load('custom.json');literal=load('oracle.json');assert len(cases)==17 and [a['id'] for a in report['attempts']]==[c['id'] for c in cases]
 for c,a in zip(cases,report['attempts']):assert json.loads(a['raw']['input_json'])==c['input'];audit(a['raw'],literal.get(c['id']))
 checks.append('17 real OS producer processes / independent oracle / all FD-path traces')
 checks.append('syscall args/results, descriptor allocation/reuse, bytes, inode/nlink, spans, close/EBADF')
 browser=load('evidence/browser.json');assert len(browser['cases'])==17
 for c,row in zip(cases,browser['cases']):
  assert row['id']==c['id'] and row['raw']==row['receipt'];assert json.loads(row['raw']['input_json'])==c['input'];audit(row['raw'],literal.get(c['id']))
  r=row['raw']['result'];assert row['status']==r['status']+' / exit='+str(row['raw']['exit']);assert row['answer']==answer(r);assert len(row['panels'])==len(r['runs']);assert len(row['syscall_texts'])==len(r['runs'])
  for panel,run,calls in zip(row['panels'],r['runs'],row['syscall_texts']):
   assert panel['label']==run['label'] and panel['state']==run['trace'][-1]
   last=run['trace'][-1];assert panel['nodes']==[dict(key=key,text=j(last[key])) for key in ['old_fd','pathname','new_fd','prepared_path']]
   assert panel['rows']==[[tr['phase'],j(tr['old_fd']),j(tr['pathname']),j(tr['new_fd']),j(tr['prepared_path'])] for tr in run['trace']]
   assert json.loads(calls)==run['syscalls']
   assert panel['summary']=='fsync_calls='+j(run['fsync_calls'])+'gap_callback_count='+str(run['gap_callback_count'])+'exception='+j(run['exception'])+'cleanup='+j(run['cleanup'])+'identities='+j(run['identities'])+'fd_numbers='+j(run['fd_numbers'])
 checks.append('17 UI raw/receipt, diagram nodes, all trace cells and syscall text, answers')
 controls={c['id']:c for c in browser['controls']};assert len(controls)==8
 for id in ['prediction-clears','input-clears','case-clears','reset-clears','held','stale-ignored','http503']:assert controls[id]['raw'] is None and controls[id]['panels']==[]
 assert controls['stale-ignored']['status']=='旧結果を無視: 1';assert controls['http503']['status']=='HTTP_ERROR 503';row=controls['invalid-path'];assert row['raw']==row['receipt'];audit(row['raw']);assert row['raw']['exit']==2 and row['panels']==[] and row['raw']['result']['mutation_started'] is False
 checks.append('8 editor/reset/held/stale/503/path refusal controls')
 wrap=load('evidence/wrap-review.json');assert [r['id'] for r in wrap['cases']]==['baseline','new-512','both-empty']
 for row in wrap['cases']:
  c=next(c for c in cases if c['id']==row['id']);assert row['raw']==row['receipt'];assert json.loads(row['raw']['input_json'])==c['input'];audit(row['raw'],literal.get(c['id']))
  for key,width in [('desktop',1280),('narrow',390)]:
   layout=row[key];assert layout['viewport']==width and layout['documentWidth']<=width
   assert layout['answerScrollWidth']<=layout['answerClientWidth'] and layout['overflowWrap']=='anywhere'
   assert layout['answer']==answer(row['raw']['result'])==next(r for r in browser['cases'] if r['id']==row['id'])['answer']
   assert len(layout['answerLines'])>=2 and all(line['width']<=layout['answerClientWidth'] for line in layout['answerLines'])
   assert [r['state'] for r in layout['panels']]==[r['trace'][-1] for r in row['raw']['result']['runs']]
  assert len(row['narrow']['answerLines'])>len(row['desktop']['answerLines'])
 for n,v in load('evidence/wrap-numerical-preservation.json').items():assert h(P/n)==v['sha256'] and (P/n).stat().st_mtime_ns==v['mtime_ns'],n
 old=load('evidence/old61-reconstruction.json');assert old['status']=='passed' and old['count_with_binding']==61
 for n,v in old['files'].items():assert h(P/v['source'])==v['sha256'],n
 checks.append('3 scoped UI cases at actual 1280/390px; full answers unchanged/wrapped; old61 reconstructable; numerical hashes/mtimes preserved')

 assert len(browser['documents'])==14
 for row in browser['documents']:assert row['sha256']==h(P/row['file']) and row['body']==(P/row['file']).read_text()
 assert len(browser['primary'])==3 and all(r['observed'] for r in browser['primary'])
 checks.append('14 source/Skill/current/Subject viewers; 3 Python primary section locators')
 n=negatives();assert n==load('evidence/negative.json') and n['status']=='passed';checks.append('26 meaningful output mutants / 13 pre-operation refusal subprocesses')
 return dict(status='passed',checks=checks,failures=[],completed=datetime.datetime.now(datetime.timezone.utc).isoformat(),cases=17,browser_cases=17,runs=sum(len(a['raw']['result']['runs']) for a in report['attempts']),trace_rows=sum(len(r['trace']) for a in report['attempts'] for r in a['raw']['result']['runs']))
if __name__=='__main__':
 try:r=main()
 except Exception as e:r=dict(status='failed',reason=str(e),kind=type(e).__name__)
 if sys.argv[1:]==['--record']:
  f=P/'evidence/verification.json'
  if f.exists() and r['status']=='failed':(P/'evidence/verification-previous.json').write_bytes(f.read_bytes())
  f.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps(r,ensure_ascii=False));sys.exit(r['status']!='passed')
