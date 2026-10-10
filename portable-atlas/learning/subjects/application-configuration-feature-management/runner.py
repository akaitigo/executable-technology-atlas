import argparse,copy,hashlib,json,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
BASE={'mode':'strict','env':{},'task':{},'actors':['alpha','beta','gamma','delta']}
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def cases():
    values={
    'defaults':{},
    'env-overrides':{'env':{'APP_TIMEOUT_MS':'2000','APP_FLAG_ENABLED':'false','APP_ROLLOUT_PERCENT':'25'}},
    'task-over-env':{'env':{'APP_TIMEOUT_MS':'2000','APP_FLAG_ENABLED':'false'},'task':{'timeout_ms':3000,'flag_enabled':True,'rollout_percent':75,'retries':5}},
    'strict-false':{'env':{'APP_FLAG_ENABLED':'false'},'task':{'rollout_percent':100}},
    'truthiness-bug':{'mode':'truthiness-bug','env':{'APP_FLAG_ENABLED':'false'},'task':{'rollout_percent':100}},
    'zero-rollout':{'task':{'rollout_percent':0}},
    'full-rollout':{'task':{'rollout_percent':100}},
    'stable-repeat':{'actors':['alpha','beta','gamma','delta','alpha']},
    'invalid-env-bool':{'env':{'APP_FLAG_ENABLED':'TRUE'}},
    'invalid-env-int':{'env':{'APP_TIMEOUT_MS':'oops'}},
    'invalid-timeout-range':{'task':{'timeout_ms':0}},
    'invalid-rollout-range':{'task':{'rollout_percent':101}},
    'bool-as-integer':{'task':{'retries':True}},
    'unknown-secret-field':{'task':{'api_key':'EXAMPLE_NOT_A_SECRET'}},
    'unknown-env-field':{'env':{'APP_SECRET':'EXAMPLE_NOT_A_SECRET'}},
    'task-string-false':{'task':{'flag_enabled':'false'}},
    'lower-config-boundary':{'task':{'timeout_ms':1,'retries':0,'rollout_percent':0}},
    'upper-config-boundary':{'task':{'timeout_ms':5000,'retries':5,'rollout_percent':100}}
    };return {k:copy.deepcopy(BASE)|v for k,v in values.items()}
def record():
    ident=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'observations'/ident;folder.mkdir(parents=True);started=now();runs=[]
    for key,request in cases().items():
        case=folder/key;case.mkdir();write(case/'input.json',request);stdin=json.dumps(request,ensure_ascii=False);began=now();p=subprocess.run([sys.executable,'evaluator.py',str((case/'result.json').relative_to(ROOT))],cwd=ROOT,input=stdin,text=True,capture_output=True)
        command={'argv':['python3','evaluator.py',str((case/'result.json').relative_to(ROOT))],'started_at':began,'completed_at':now(),'stdin':stdin,'stdout':p.stdout,'stderr':p.stderr,'exit_code':p.returncode}
        for s in ('stdin','stdout','stderr'):command[s+'_digest']=sha(command[s].encode())
        write(case/'command.json',command);write(case/'trace.json',[json.loads(line) for line in p.stdout.splitlines()]);runs.append({'id':key,'exit_code':p.returncode})
    names=['evaluator.py','runner.py','checker.py','test_negative.py','preview.py','index.html','README.md','sources.json','coverage.json','skills/atlas-application-configuration-feature-management/SKILL.md','skills/atlas-application-configuration-feature-management/route.py']
    write(folder/'observation.json',{'execution_id':ident,'started_at':started,'completed_at':now(),'environment':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine()},'source_bindings':{n:sha((ROOT/n).read_bytes()) for n in names},'runs':runs,'fictional_cloud_model':True,'os_environment_read_or_changed':False,'system_configuration_changed':False,'real_SLA_guarantee':False,'external_services':0})
    began=now();p=subprocess.run([sys.executable,'checker.py','--oracle',str(folder.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr)
    write(folder/'oracle.json',json.loads(p.stdout));write(folder/'oracle-command.json',{'argv':['python3','checker.py','--oracle',str(folder.relative_to(ROOT))],'started_at':began,'completed_at':now(),'stdout':p.stdout,'stderr':p.stderr,'exit_code':p.returncode,'stdout_digest':sha(p.stdout.encode()),'stderr_digest':sha(p.stderr.encode())})
    write(folder/'artifact-index.json',{p.relative_to(folder).as_posix():{'digest':sha(p.read_bytes()),'size':p.stat().st_size} for p in folder.rglob('*') if p.is_file()});write(ROOT/'current.json',{'directory':str(folder.relative_to(ROOT))});print(json.dumps({'directory':str(folder.relative_to(ROOT)),'cases':len(runs)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
    if args.record:record()
    else:raise SystemExit(subprocess.call([sys.executable,str(ROOT/'checker.py')]))
