import pathlib,json,hashlib,sys,itertools
R=pathlib.Path(__file__).resolve().parent
def contract(x):
 if type(x)!=dict or set(x)!=set(['policy','completion','order','generation','oldPayload','newPayload']) or x['policy'] not in ['guarded','cancel-release-fault'] or x['completion'] not in ['success','aborted']:return False
 if type(x['generation']) is not int or x['generation']<1 or x['generation']>9:return False
 if type(x['order']) is not list or len(x['order'])!=4 or x['order'][0]!='submit' or any(type(v)!=str for v in x['order']) or set(x['order'])!=set(['submit','cancel','complete','reuse']):return False
 return all(type(x[k])==str and 0<len(x[k])<=40 and all(32<=ord(c)<=126 for c in x[k]) for k in ['oldPayload','newPayload'])
def expected(x):
 order=x['order'];donePos=order.index('complete');cancelPos=order.index('cancel');reusePos=order.index('reuse');fault=x['policy']=='cancel-release-fault';allows=donePos<reusePos or fault and cancelPos<reusePos;trace=[]
 for i,action in enumerate(order):
  done=donePos<=i;cancelled=cancelPos<=i and cancelPos<donePos;attempt=reusePos<=i;reused=attempt and allows;cross=done and reused and reusePos<donePos;g=x['generation']+int(reused)
  owner=(None if cross else 'application') if reused else None if done or fault and cancelled else 'A'
  payload=(x['oldPayload'] if cross and x['completion']=='success' else x['newPayload']) if reused else x['oldPayload'] if done and x['completion']=='success' else 'empty'
  status=x['completion'] if done and (not reused or cross) else None
  state={'buffer':{'generation':g,'owner':owner,'status':status,'payload':payload},'operationA':{'submittedGeneration':x['generation'],'pending':not done,'cancelRequested':cancelled,'status':x['completion'] if done else None},'interference':bool(cross),'reuseAllowed':bool(allows) if attempt else None}
  result='SUBMITTED' if action=='submit' else ('NOT_PENDING' if donePos<cancelPos else 'REQUESTED') if action=='cancel' else ('REUSE_ALLOWED' if allows else 'REUSE_REJECTED') if action=='reuse' else 'COMPLETED_'+x['completion'].upper();trace.append({'action':action,'result':result,'state':state})
 return {'observed':True,'reason':None,'trace':trace,'summary':trace[-1]['state']}
def audit(c):
 try:x=json.loads(c['inputRaw'])
 except json.JSONDecodeError:
  assert c['exitCode']==3 and c['stdout']=='' and c['stderr'].startswith('JSONDecodeError:');return {'outcome':'EXECUTION_FAILURE','summary':None}
 o=json.loads(c['stdout'])
 if not contract(x):
  assert c['exitCode']==2 and o['observed'] is False and o['summary'] is None and o['trace']==[];return {'outcome':'REFUSED','summary':None}
 e=expected(x);assert c['exitCode']==0 and c['stderr']=='' and o==e;return {'outcome':'OBSERVED','summary':e['summary']}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def table(o):
 return [[t['action'],t['result'],t['state']['buffer']['generation'],t['state']['buffer']['owner'],t['state']['operationA']['pending'],t['state']['operationA']['cancelRequested'],t['state']['buffer']['status'],t['state']['buffer']['payload'],t['state']['interference'],t['state']['reuseAllowed']] for t in o['trace']]

LITERAL={'guarded-success': [['submit', 'SUBMITTED', 1, 'A', True, False, None, 'empty', False, None], ['cancel', 'REQUESTED', 1, 'A', True, True, None, 'empty', False, None], ['reuse', 'REUSE_REJECTED', 1, 'A', True, True, None, 'empty', False, False], ['complete', 'COMPLETED_SUCCESS', 1, None, False, True, 'success', 'A-result', False, False]], 'guarded-aborted': [['submit', 'SUBMITTED', 1, 'A', True, False, None, 'empty', False, None], ['cancel', 'REQUESTED', 1, 'A', True, True, None, 'empty', False, None], ['reuse', 'REUSE_REJECTED', 1, 'A', True, True, None, 'empty', False, False], ['complete', 'COMPLETED_ABORTED', 1, None, False, True, 'aborted', 'empty', False, False]], 'fault-success': [['submit', 'SUBMITTED', 1, 'A', True, False, None, 'empty', False, None], ['cancel', 'REQUESTED', 1, None, True, True, None, 'empty', False, None], ['reuse', 'REUSE_ALLOWED', 2, 'application', True, True, None, 'B-data', False, True], ['complete', 'COMPLETED_SUCCESS', 2, None, False, True, 'success', 'A-result', True, True]], 'fault-aborted': [['submit', 'SUBMITTED', 1, 'A', True, False, None, 'empty', False, None], ['cancel', 'REQUESTED', 1, None, True, True, None, 'empty', False, None], ['reuse', 'REUSE_ALLOWED', 2, 'application', True, True, None, 'B-data', False, True], ['complete', 'COMPLETED_ABORTED', 2, None, False, True, 'aborted', 'B-data', True, True]]}
FINAL={'guarded-success': [1, None, 'success', 'A-result', False, False, True], 'guarded-aborted': [1, None, 'aborted', 'empty', False, False, True], 'fault-success': [2, None, 'success', 'A-result', True, True, True], 'fault-aborted': [2, None, 'aborted', 'B-data', True, True, True], 'complete-before-reuse': [2, 'application', None, 'B-data', False, True, True], 'fault-complete-before-reuse': [2, 'application', None, 'B-data', False, True, True], 'cancel-after-complete': [2, 'application', None, 'B-data', False, True, False], 'fault-cancel-after-complete': [2, 'application', None, 'B-data', False, True, False], 'reuse-before-cancel': [1, None, 'success', 'A-result', False, False, True], 'variable-generation4': [5, None, 'success', 'old-four', True, True, True]}
def check(root=R):
 run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text());assert (run/'result.json').read_bytes()==(run/'stdout.json').read_bytes()
 for n,h in d['sourceHashes'].items():assert sha(root/n)==h
 for n,v in json.loads((run/'artifacts.json').read_text())['files'].items():assert sha(run/n)==v['sha256'] and (run/n).stat().st_size==v['bytes']
 req=json.loads((root/'requests.json').read_text());oracle=json.loads((root/'oracle.json').read_text());assert oracle['requests']==req and oracle['literalOperationBufferTable']==LITERAL and oracle['literalFinal']==FINAL;assert list(req)==[c['id'] for c in d['cases']]
 for c in d['cases']:
  f=run/c['id'];assert (f/'input.txt').read_text()==c['inputRaw'] and (f/'stdout.txt').read_text()==c['stdout'] and (f/'stderr.txt').read_text()==c['stderr'] and json.loads((f/'command.json').read_text())==c;x=req[c['id']];assert c['inputRaw']==(x['rawInput'] if 'rawInput' in x else json.dumps(x,sort_keys=True)+'\n');assert json.loads(c['auditCommand']['inputRaw'])=={k:c[k] for k in ['inputRaw','argv','startedUtc','endedUtc','exitCode','stdout','stderr']}
  assert c['auditCommand']['stdout']==c['auditStdout'] and c['auditCommand']['stderr']==c['auditStderr'] and c['auditCommand']['exitCode']==c['auditExitCode'];assert (f/'audit-stdout.txt').read_text()==c['auditStdout'] and (f/'audit-stderr.txt').read_text()==c['auditStderr'] and json.loads((f/'audit-command.json').read_text())==c['auditCommand']
  for n,h in c['sourceHashes'].items():assert sha(root/n)==h
  a=audit(c);assert c['auditExitCode']==0 and json.loads(c['auditStdout'])==a and c['auditStderr']==''
  if c['id'] in LITERAL:assert table(json.loads(c['stdout']))==LITERAL[c['id']]
  if c['id'] in FINAL:
   s=a['summary'];b=s['buffer'];assert [b['generation'],b['owner'],b['status'],b['payload'],s['interference'],s['reuseAllowed'],s['operationA']['cancelRequested']]==FINAL[c['id']]
  elif c['id'].startswith('refused-'):assert a['outcome']=='REFUSED'
  else:assert c['id']=='execution-failure' and a['outcome']=='EXECUTION_FAILURE'
 return len(d['cases'])
if __name__=='__main__':
 if sys.argv[1:]==['--audit']:
  try:print(json.dumps(audit(json.load(sys.stdin))))
  except (AssertionError,ValueError,KeyError,TypeError) as e:print('AuditError: '+type(e).__name__,file=sys.stderr);sys.exit(5)
 elif not sys.argv[1:]:print('PASS '+str(check())+' conditions; literal operation/buffer ownership + independent order-position oracle')
 else:sys.exit(2)
