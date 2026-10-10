# Independent expected transition table + identity/set assessment, no model/build import.
import json,sys,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parent
TABLE={'REPRO':(2,3,'SUCCESS',4,2),'EQUAL':(2,2,'SUCCESS',4,2),'SHORT':(2,1,'TIMEOUT',None,1),'ZERO':(2,0,'TIMEOUT',None,0),'VALUE0':(0,3,'SUCCESS',0,2),'VALUE3':(3,3,'SUCCESS',6,2),'COINCIDENCE':(1,3,'SUCCESS',2,2)}
def sha(n):return hashlib.sha256((P/n).read_bytes()).hexdigest()
def source(b):return 'build_'+b.replace('-','_')+'.py'
def testset(record,build,suite):
 if build is None:assert record is None;return
 assert record['build']==build and record['source']==source(build) and record['source_sha256']==sha(source(build));ids=[i for i in TABLE if i in suite];assert [t['id'] for t in record['tests']]==ids;fail=[];passed=[]
 for row in record['tests']:
  v,d,status,out,ticks=TABLE[row['id']];expected=dict(status=status,output=out,logical_ticks=ticks)
  if build=='bad':observed=dict(status='SUCCESS',output=v+1,logical_ticks=1)
  elif build=='partial' and d==2:observed=dict(status='TIMEOUT',output=None,logical_ticks=2)
  else:observed=expected
  assert row['expected']==expected and row['actual']==observed and json.loads(row['stdout'])==observed and row['stderr']=='' and row['exit']==0
  assert json.loads(row['stdin'])==dict(value=v,deadline_ticks=d) and row['argv']==['python3','-B',source(build)] and row['build_source_sha256']==sha(source(build)) and row['tests_sha256']==sha('tests.json')
  assert datetime.datetime.fromisoformat(row['completed'])>=datetime.datetime.fromisoformat(row['started']);correct=observed==expected;assert row['passed']==correct;(passed if correct else fail).append(row['id'])
 assert record['failed']==sorted(fail) and record['passed']==sorted(passed)
def check(r,x,literal=None):
 if literal and 'status' in literal:assert r==literal;return
 assert r['status']=='OBSERVED';testset(r['current'],x['current_build'] if x['retest'] else None,x['suite']);testset(r['evidence'],x['evidence_build'],x['suite']);digest=sha(source(x['current_build']));chosen=r['current'] if x['retest'] else r['evidence'];matches=chosen is not None and (chosen['build'],chosen['source_sha256'])==(x['current_build'],digest);missing=sorted(set(TABLE)-set(t['id'] for t in chosen['tests'])) if chosen else sorted(TABLE);complete=missing==[];allpassed=chosen is not None and chosen['failed']==[];verified=matches and complete and allpassed
 if not x['action_done']:decision='ACTION_OPEN'
 elif chosen is None:decision='UNVERIFIED'
 elif not matches:decision='STALE_PROOF'
 elif chosen['failed']:decision='INEFFECTIVE'
 elif missing:decision='SUITE_INCOMPLETE'
 else:decision='VERIFIED_FINITE'
 expected=dict(status='OBSERVED',incident='INC-DOUBLE',action='ACT-DOUBLE',input=x,currentSourceDigest=digest,current=r['current'],evidence=r['evidence'],chosen='current' if r['current'] is not None else 'evidence' if r['evidence'] is not None else None,matchesCurrent=matches,completeSuite=complete,allPassed=allpassed,missingTests=missing,behaviorVerified=verified,actionEffective=bool(x['action_done'] and verified),decision=decision,testsExecuted=sum(len(v['tests']) for v in [r['current'],r['evidence']] if v),approval='UNCONFIRMED',productionEffectiveness='UNCONFIRMED',clock='synthetic logical ticks; real Python tests');assert r==expected
 if literal:assert decision==literal['decision'] and (r['current']['failed'] if r['current'] else [])==literal['current_failed'] and (r['evidence']['failed'] if r['evidence'] else [])==literal['evidence_failed']
if __name__=='__main__':
 a=json.loads(sys.stdin.read());check(a['result'],a['input']);print(json.dumps(dict(status='passed',independent=True)))
