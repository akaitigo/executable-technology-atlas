import json,sys,subprocess,hashlib,datetime
from pathlib import Path
P=Path(__file__).resolve().parent;BUILDS=['bad','partial','fixed-v1','fixed-v2'];TESTS=json.loads((P/'tests.json').read_text());IDS=[t['id'] for t in TESTS]
class Refused(Exception):pass
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def source(build):return 'build_'+build.replace('-','_')+'.py'
def sha(name):return hashlib.sha256((P/name).read_bytes()).hexdigest()
def validate(x):
 if not isinstance(x,dict) or set(x)!=set(['current_build','action_done','evidence_build','retest','suite']):raise Refused('FIELDS')
 if x['current_build'] not in BUILDS or (x['evidence_build'] is not None and x['evidence_build'] not in BUILDS):raise Refused('BUILD')
 if type(x['action_done'])!=bool or type(x['retest'])!=bool:raise Refused('FLAGS')
 if not isinstance(x['suite'],list) or len(x['suite'])>7 or any(not isinstance(v,str) or v not in IDS for v in x['suite']) or len(set(x['suite']))!=len(x['suite']):raise Refused('SUITE')
def run(build,suite):
 rows=[];src=source(build)
 for t in TESTS:
  if t['id'] not in suite:continue
  data=json.dumps(dict(value=t['value'],deadline_ticks=t['deadline_ticks']));started=utc();child=subprocess.run([sys.executable,'-B',src],input=data,text=True,capture_output=True,cwd=P);actual=json.loads(child.stdout);passed=child.returncode==0 and actual==t['expected']
  rows.append(dict(id=t['id'],argv=['python3','-B',src],stdin=data,started=started,completed=utc(),exit=child.returncode,stdout=child.stdout,stderr=child.stderr,expected=t['expected'],actual=actual,passed=passed,build_source_sha256=sha(src),tests_sha256=sha('tests.json')))
 return dict(build=build,source=src,source_sha256=sha(src),tests=rows,failed=sorted(t['id'] for t in rows if not t['passed']),passed=sorted(t['id'] for t in rows if t['passed']))
def process(x):
 validate(x);evidence=run(x['evidence_build'],x['suite']) if x['evidence_build'] else None;current=run(x['current_build'],x['suite']) if x['retest'] else None;chosen=current if x['retest'] else evidence;currentDigest=sha(source(x['current_build']));matches=chosen is not None and chosen['build']==x['current_build'] and chosen['source_sha256']==currentDigest;missing=sorted(set(IDS)-set(t['id'] for t in chosen['tests'])) if chosen else sorted(IDS);complete=not missing;allpass=chosen is not None and len(chosen['failed'])==0;verified=matches and complete and allpass
 decision='ACTION_OPEN' if not x['action_done'] else 'UNVERIFIED' if chosen is None else 'STALE_PROOF' if not matches else 'INEFFECTIVE' if not allpass else 'SUITE_INCOMPLETE' if not complete else 'VERIFIED_FINITE'
 return dict(status='OBSERVED',incident='INC-DOUBLE',action='ACT-DOUBLE',input=x,currentSourceDigest=currentDigest,current=current,evidence=evidence,chosen='current' if current is not None else 'evidence' if evidence is not None else None,matchesCurrent=matches,completeSuite=complete,allPassed=allpass,missingTests=missing,behaviorVerified=verified,actionEffective=bool(x['action_done'] and verified),decision=decision,testsExecuted=sum(len(r['tests']) for r in [current,evidence] if r),approval='UNCONFIRMED',productionEffectiveness='UNCONFIRMED',clock='synthetic logical ticks; real Python tests')
if __name__=='__main__':
 try:
  x=json.loads(sys.stdin.read())
  if '--fail' in sys.argv:raise RuntimeError('injected evaluator error')
  out=process(x);code=0
 except (Refused,json.JSONDecodeError) as e:out=dict(status='INPUT_REFUSED',reason=str(e) if isinstance(e,Refused) else 'JSON');code=2
 except Exception as e:out=dict(status='EXECUTION_FAILURE',reason=type(e).__name__);code=1
 print(json.dumps(out));sys.exit(code)
