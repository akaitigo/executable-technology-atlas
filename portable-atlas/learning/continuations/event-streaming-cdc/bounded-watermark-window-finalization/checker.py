import pathlib,json,hashlib,sys
R=pathlib.Path(__file__).resolve().parent
def contract(x):
 if not isinstance(x,dict) or set(x)!=set(['mode','lag','allowedLateness','events']) or x['mode'] not in ['min','max-fault']:return False
 for key in ['lag','allowedLateness']:
  if type(x[key]) is not int or x[key]<0 or x[key]>20:return False
 if type(x['events']) is not list or not 1<=len(x['events'])<=12:return False
 ids=[]
 for e in x['events']:
  if type(e) is not dict or set(e)!=set(['id','partition','time','value']):return False
  if type(e['id']) is not str or not 0<len(e['id'])<=40 or e['id'] in ids:return False
  ids.append(e['id'])
  if e['partition'] not in ['p0','p1']:return False
  if any(type(e[k]) is not int or e[k]<0 or e[k]>100 for k in ['time','value']):return False
 return True
def reconstruct(x):
 es=x['events'];lag=x['lag'];A=x['allowedLateness'];watermarks=[];accepted=[];dropped=[];lateIDs=[];trace=[];windowHistory=[]
 for i,e in enumerate(es):
  before=watermarks[-1] if watermarks else None;start=(e['time']//10)*10;late=before is not None and e['time']<before;ok=before is None or before<start+10+A
  if ok:accepted.append(e)
  else:dropped.append(e['id'])
  if ok and late:lateIDs.append(e['id'])
  prefix=es[:i+1];maxes={p:max([v['time'] for v in prefix if v['partition']==p],default=None) for p in ['p0','p1']};pw={p:None if maxes[p] is None else maxes[p]-lag for p in maxes};vals=[v for v in pw.values() if v is not None];candidate=(None if None in pw.values() else min(vals)) if x['mode']=='min' else max(vals);wm=candidate if before is None else before if candidate is None else max(before,candidate);watermarks.append(wm)
  starts=sorted(set((v['time']//10)*10 for v in accepted));windows=[];fires=[];finals=[];previous=windowHistory[-1] if windowHistory else []
  for s in starts:
   members=[v for v in accepted if s<=v['time']<s+10];total=sum(v['value'] for v in members);old=next((w for w in previous if w['start']==s),None);fired=(old is not None and old['initialFired']) or (wm is not None and wm>=s+10);final=(old is not None and old['finalized']) or (wm is not None and wm>=s+10+A);finalstep=old['finalizedStep'] if old and old['finalized'] else i+1 if final else None
   if ok and start==s and old and old['initialFired']:fires.append({'start':s,'sum':total,'kind':'late-update'})
   if fired and (old is None or not old['initialFired']):fires.append({'start':s,'sum':total,'kind':'initial'})
   if final and (old is None or not old['finalized']):finals.append(s)
   windows.append({'start':s,'end':s+10,'sum':total,'ids':[v['id'] for v in members],'initialFired':bool(fired),'finalized':bool(final),'finalizedStep':finalstep})
  # producer emits late update before initial firings (different windows); normalize same deterministic order.
  fires.sort(key=lambda f:(f['kind']=='initial',f['start']));windowHistory.append(windows);trace.append({'step':i+1,'event':e,'windowStart':start,'beforeWatermark':before,'late':late,'decision':'ACCEPT' if ok else 'DROP_FINALIZED','maxSeen':maxes,'partitionWatermarks':pw,'watermark':wm,'firedNow':fires,'finalizedNow':finals,'windows':windows})
 return {'observed':True,'reason':None,'trace':trace,'summary':{'accepted':[e['id'] for e in accepted],'dropped':dropped,'lateAccepted':lateIDs,'watermark':watermarks[-1],'windows':windowHistory[-1],'mode':x['mode'],'lag':lag,'allowedLateness':A,'endFlush':False}}
def audit(c):
 try:x=json.loads(c['inputRaw'])
 except json.JSONDecodeError:
  assert c['exitCode']==3 and c['stdout']=='' and c['stderr'].startswith('JSONDecodeError:');return {'outcome':'EXECUTION_FAILURE','summary':None,'maxFaultLoss':None}
 o=json.loads(c['stdout'])
 if not contract(x):
  assert c['exitCode']==2 and o['observed'] is False and o['summary'] is None and o['trace']==[];return {'outcome':'REFUSED','summary':None,'maxFaultLoss':None}
 expected=reconstruct(x);assert c['exitCode']==0 and c['stderr']=='' and o==expected
 baseline=reconstruct(dict(x,mode='min'));lost=[i for i in baseline['summary']['accepted'] if i not in o['summary']['accepted']]
 return {'outcome':'OBSERVED','summary':expected['summary'],'maxFaultLoss':lost,'minReferenceSummary':baseline['summary']}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

LITERAL={'min-complete': {'watermarks': [None, -1, -1, 6, 18], 'accepted': ['e1', 'e2', 'e3', 'e4', 'e5'], 'dropped': [], 'lateAccepted': [], 'windows': [[0, 7, ['e1', 'e2', 'e4'], True, 5], [20, 8, ['e3', 'e5'], False, None]]}, 'max-fault': {'watermarks': [0, 0, 18, 18, 18], 'accepted': ['e1', 'e2', 'e3', 'e5'], 'dropped': ['e4'], 'lateAccepted': [], 'windows': [[0, 3, ['e1', 'e2'], True, 3], [20, 8, ['e3', 'e5'], False, None]]}, 'stalled-partition': {'watermarks': [None, -1, -1], 'accepted': ['e1', 'e2', 'e3'], 'dropped': [], 'lateAccepted': [], 'windows': [[0, 3, ['e1', 'e2'], False, None], [20, 3, ['e3'], False, None]]}, 'unseen-partition': {'watermarks': [None, None], 'accepted': ['e1', 'e3'], 'dropped': [], 'lateAccepted': [], 'windows': [[0, 1, ['e1'], False, None], [20, 3, ['e3'], False, None]]}, 'lag0': {'watermarks': [None, 1, 1, 8, 20], 'accepted': ['e1', 'e2', 'e3', 'e4', 'e5'], 'dropped': [], 'lateAccepted': [], 'windows': [[0, 7, ['e1', 'e2', 'e4'], True, 5], [20, 8, ['e3', 'e5'], False, None]]}, 'reordered': {'watermarks': [None, -1, 0, 6, 18], 'accepted': ['e1', 'e2', 'e4', 'e3', 'e5'], 'dropped': [], 'lateAccepted': [], 'windows': [[0, 7, ['e1', 'e2', 'e4'], True, 5], [20, 8, ['e3', 'e5'], False, None]]}, 'grace-late-update': {'watermarks': [None, 2, 2, 10, 10, 10, 13], 'accepted': ['e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7'], 'dropped': [], 'lateAccepted': ['e5'], 'windows': [[0, 8, ['e1', 'e2', 'e5'], True, 7], [10, 20, ['e3', 'e4', 'e6', 'e7'], False, None]]}, 'deadline-boundary': {'watermarks': [None, 2, 2, 10, 10, 10, 13, 13], 'accepted': ['e1', 'e2', 'e3', 'e4', 'e5', 'e6', 'e7'], 'dropped': ['e8'], 'lateAccepted': ['e5'], 'windows': [[0, 8, ['e1', 'e2', 'e5'], True, 7], [10, 20, ['e3', 'e4', 'e6', 'e7'], False, None]]}, 'no-grace-boundary': {'watermarks': [None, 2, 2, 10, 10], 'accepted': ['e1', 'e2', 'e3', 'e4'], 'dropped': ['e5'], 'lateAccepted': [], 'windows': [[0, 3, ['e1', 'e2'], True, 4], [10, 7, ['e3', 'e4'], False, None]]}, 'within-lag': {'watermarks': [None, 6, 6, 6, 18], 'accepted': ['e1', 'e2', 'e3', 'e4', 'e5'], 'dropped': [], 'lateAccepted': [], 'windows': [[0, 6, ['e1', 'e2', 'e3'], True, 5], [20, 9, ['e4', 'e5'], False, None]]}}
def check(root=R):
 run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text());assert (run/'result.json').read_bytes()==(run/'stdout.json').read_bytes()
 for n,h in d['sourceHashes'].items():assert sha(root/n)==h,n
 for n,v in json.loads((run/'artifacts.json').read_text())['files'].items():assert sha(run/n)==v['sha256'] and (run/n).stat().st_size==v['bytes']
 req=json.loads((root/'requests.json').read_text());oracle=json.loads((root/'oracle.json').read_text());assert oracle['requests']==req and oracle['literal']==LITERAL;assert list(req)==[c['id'] for c in d['cases']]
 for c in d['cases']:
  f=run/c['id'];assert (f/'input.txt').read_text()==c['inputRaw'] and (f/'stdout.txt').read_text()==c['stdout'] and (f/'stderr.txt').read_text()==c['stderr'] and json.loads((f/'command.json').read_text())==c
  x=req[c['id']];assert c['inputRaw']==(x['rawInput'] if 'rawInput' in x else json.dumps(x,sort_keys=True)+'\n');assert c['argv']==['python3','-B','model.py']
  assert c['auditCommand']['argv']==['python3','-B','checker.py','--audit'];assert json.loads(c['auditCommand']['inputRaw'])=={k:c[k] for k in ['inputRaw','argv','startedUtc','endedUtc','exitCode','stdout','stderr']}
  assert c['auditCommand']['stdout']==c['auditStdout'] and c['auditCommand']['stderr']==c['auditStderr'] and c['auditCommand']['exitCode']==c['auditExitCode'];assert (f/'audit-stdout.txt').read_text()==c['auditStdout'] and (f/'audit-stderr.txt').read_text()==c['auditStderr'] and json.loads((f/'audit-command.json').read_text())==c['auditCommand']
  for n,h in c['sourceHashes'].items():assert sha(root/n)==h
  a=audit(c);assert c['auditExitCode']==0 and json.loads(c['auditStdout'])==a and c['auditStderr']==''
  if c['id'] in LITERAL:
   l=LITERAL[c['id']];o=json.loads(c['stdout']);s=o['summary'];assert [t['watermark'] for t in o['trace']]==l['watermarks'];assert [s[k] for k in ['accepted','dropped','lateAccepted']]==[l[k] for k in ['accepted','dropped','lateAccepted']];assert [[w['start'],w['sum'],w['ids'],w['initialFired'],w['finalizedStep']] for w in s['windows']]==l['windows']
  elif c['id'].startswith('refused-'):assert a['outcome']=='REFUSED'
  else:assert c['id']=='execution-failure' and a['outcome']=='EXECUTION_FAILURE'
 return len(d['cases'])
if __name__=='__main__':
 if sys.argv[1:]==['--audit']:
  try:print(json.dumps(audit(json.load(sys.stdin))))
  except (AssertionError,ValueError,KeyError,TypeError) as e:print('AuditError: '+type(e).__name__,file=sys.stderr);sys.exit(5)
 elif not sys.argv[1:]:print('PASS '+str(check())+' conditions; literal windows/watermarks + independent prefix oracle; no producer import')
 else:sys.exit(2)
