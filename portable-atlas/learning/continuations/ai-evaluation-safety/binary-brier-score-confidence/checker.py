import pathlib,json,hashlib,sys,math
R=pathlib.Path(__file__).resolve().parent
# Independently written integer numerator oracle, no producer import and no Fraction.
def rational(n,d=1):
 g=math.gcd(n,d);n//=g;d//=g;return str(n) if d==1 else str(n)+'/'+str(d)
def contract(x):
 if type(x)!=dict or set(x)!={'mode','samples'} or x['mode'] not in ['probability','threshold-fault']:return False
 ss=x['samples']
 if type(ss)!=list or not 1<=len(ss)<=8:return False
 ids=[]
 for s in ss:
  if type(s)!=dict or set(s)!={'id','percent','label'}:return False
  if type(s['id'])!=str or not 0<len(s['id'])<=40 or s['id'] in ids:return False
  ids.append(s['id'])
  if type(s['percent'])!=int or s['percent']<0 or s['percent']>100:return False
  if type(s['label'])!=int or s['label'] not in [0,1]:return False
 return True
def audit(c):
 try:x=json.loads(c['inputRaw'])
 except json.JSONDecodeError:
  assert c['exitCode']==3 and c['stdout']=='' and c['stderr'].startswith('JSONDecodeError:');return {'outcome':'EXECUTION_FAILURE','probabilityBrier':None,'correct':None,'samples':[],'reportedScoreValid':None}
 o=json.loads(c['stdout'])
 if not contract(x):
  assert c['exitCode']==2 and o['observed'] is False and o['summary'] is None and o['samples']==[];return {'outcome':'REFUSED','probabilityBrier':None,'correct':None,'samples':[],'reportedScoreValid':None}
 assert c['exitCode']==0 and c['stderr']=='' and o['observed'] is True and o['reason'] is None
 rows=[];nums=[];usednums=[];correct=0
 for s in x['samples']:
  p=s['percent'];y=s['label'];cl=1 if p>=50 else 0;num=(p-100*y)*(p-100*y);used=100*cl if x['mode']=='threshold-fault' else p;un=(used-100*y)*(used-100*y);nums.append(num);usednums.append(un);correct+=cl==y
  expected={'id':s['id'],'percent':p,'label':y,'probability':rational(p,100),'class':cl,'usedScore':rational(used,100),'squaredError':rational(un,10000)};assert o['samples'][len(rows)]==expected;rows.append({'id':s['id'],'percent':p,'label':y,'class':cl,'probabilitySquaredError':rational(num,10000),'reportedSquaredError':rational(un,10000)})
 n=len(rows);mean=rational(sum(nums),10000*n);reported=rational(sum(usednums),10000*n)
 assert len(o['samples'])==n and o['summary']=={'count':n,'correct':correct,'accuracy':rational(correct,n),'reportedBrier':reported,'mode':x['mode'],'thresholdPercent':50}
 return {'outcome':'OBSERVED','probabilityBrier':mean,'correct':correct,'samples':rows,'reportedScoreValid':mean==reported,'reportedBrier':reported}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
LITERAL={'moderate':(['4/25','4/25'],'4/25','4/25',2,[1,0]),'confident':(['1/100','1/100'],'1/100','1/100',2,[1,0]),'overconfident-wrong':(['1/100','81/100'],'41/100','41/100',1,[1,1]),'perfect':(['0','0'],'0','0',2,[1,0]),'opposite':(['1','1'],'1','1',0,[0,1]),'threshold-fault-moderate':(['4/25','4/25'],'4/25','0',2,[1,0]),'threshold-fault-confident':(['1/100','1/100'],'1/100','0',2,[1,0]),'edited73':(['729/10000','4/25'],'2329/20000','2329/20000',2,[1,0]),'threshold50':(['1/4','1/4'],'1/4','1/4',1,[1,1])}
def check(root=R):
 run=root/(root/'CURRENT').read_text().strip();d=json.loads((run/'result.json').read_text());assert (run/'result.json').read_bytes()==(run/'stdout.json').read_bytes()
 for n,h in d['sourceHashes'].items():assert sha(root/n)==h,n
 for n,v in json.loads((run/'artifacts.json').read_text())['files'].items():assert sha(run/n)==v['sha256'] and (run/n).stat().st_size==v['bytes']
 requests=json.loads((root/'requests.json').read_text());oracle=json.loads((root/'oracle.json').read_text());assert oracle['requests']==requests;assert list(requests)==[c['id'] for c in d['cases']];assert set(oracle['literal'])==set(LITERAL)
 for c in d['cases']:
  f=run/c['id'];assert (f/'input.txt').read_text()==c['inputRaw'] and (f/'stdout.txt').read_text()==c['stdout'] and (f/'stderr.txt').read_text()==c['stderr'];assert json.loads((f/'command.json').read_text())==c
  x=requests[c['id']];expected=x['rawInput'] if 'rawInput' in x else json.dumps(x,sort_keys=True)+'\n';assert c['inputRaw']==expected
  assert json.loads(c['auditCommand']['inputRaw'])=={k:c[k] for k in ['inputRaw','argv','startedUtc','endedUtc','exitCode','stdout','stderr']};assert c['auditCommand']['stdout']==c['auditStdout'] and c['auditCommand']['stderr']==c['auditStderr'] and c['auditCommand']['exitCode']==c['auditExitCode'];assert c['argv']==['python3','-B','model.py'] and c['auditCommand']['argv']==['python3','-B','checker.py','--audit']
  for n,h in c['sourceHashes'].items():assert sha(root/n)==h
  a=audit(c);assert c['auditExitCode']==0 and json.loads(c['auditStdout'])==a and c['auditStderr']=='';assert (f/'audit-stdout.txt').read_text()==c['auditStdout'] and (f/'audit-stderr.txt').read_text()==c['auditStderr'] and json.loads((f/'audit-command.json').read_text())==c['auditCommand']
  if c['id'] in LITERAL:
   e,mean,rep,correct,classes=LITERAL[c['id']];lit=oracle['literal'][c['id']];assert lit=={'errors':e,'mean':mean,'reported':rep,'correct':correct,'classes':classes};assert [s['probabilitySquaredError'] for s in a['samples']]==e and a['probabilityBrier']==mean and a['reportedBrier']==rep and a['correct']==correct and [s['class'] for s in a['samples']]==classes
  elif c['id'].startswith('refused-'):assert a['outcome']=='REFUSED'
  else:assert c['id']=='execution-failure' and a['outcome']=='EXECUTION_FAILURE'
 return len(d['cases'])
if __name__=='__main__':
 if sys.argv[1:]==['--audit']:
  try:print(json.dumps(audit(json.load(sys.stdin))))
  except (AssertionError,ValueError,KeyError,TypeError) as e:print('AuditError: '+type(e).__name__,file=sys.stderr);sys.exit(5)
 elif not sys.argv[1:]:print('PASS '+str(check())+' conditions; literal sample errors + independent integer oracle; no producer import')
 else:sys.exit(2)
