"""Explicit --record generates raw evidence. Default invokes read-only checker."""
import argparse,copy,hashlib,json,platform,subprocess,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def raw(v):return (json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def now():return datetime.now(timezone.utc).isoformat()
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
CONTRACT={'version':1,'required':['id','category','amount','class'],'amount_range':[0,1000000],'unique':'id','reference':['products.category','categories.id'],'classes':['public','internal']}
BASE={'sources':{'products':[{'id':'p1','category':'c1','amount':100,'class':'public'},{'id':'p2','category':'c2','amount':0,'class':'internal'}],'categories':[{'id':'c1'},{'id':'c2'}]},'graph':{'products':{'parents':[],'columns':['id','category','amount','class']},'categories':{'parents':[],'columns':['id']},'validated':{'parents':['products','categories'],'columns':['id','category','amount','class']},'totals':{'parents':['validated'],'columns':['category','amount_sum','class']}},'column_lineage':[{'target':'validated.id','sources':['products.id']},{'target':'validated.category','sources':['products.category','categories.id']},{'target':'validated.amount','sources':['products.amount']},{'target':'validated.class','sources':['products.class']},{'target':'totals.category','sources':['validated.category']},{'target':'totals.amount_sum','sources':['validated.amount']},{'target':'totals.class','sources':['validated.class']}]}
def fixtures():
    cases={'normal':copy.deepcopy(BASE)}
    for key,col,value in [('lower-bound','amount',0),('upper-bound','amount',1000000),('nonnull','amount',None),('below-range','amount',-1),('above-range','amount',1000001),('duplicate-id','id','p2'),('missing-reference','category','c9'),('unknown-class','class','secret')]:
        q=copy.deepcopy(BASE);q['sources']['products'][0][col]=value;cases[key]=q
    q=copy.deepcopy(BASE);q['sources']['products']=[];cases['empty']=q
    q=copy.deepcopy(BASE);q['sources']['products'][0].update({'amount':-1,'category':'c9','class':'secret'});cases['combined-bad']=q
    q=copy.deepcopy(BASE);q['graph']['validated']['parents']=['totals'];cases['cycle']=q
    q=copy.deepcopy(BASE);q['graph']['totals']['parents']=['missing'];cases['orphan-node']=q
    q=copy.deepcopy(BASE);q['column_lineage'][5]['sources']=['validated.absent'];cases['orphan-column']=q
    bindings={'sources':{n:sha(raw(rows)) for n,rows in BASE['sources'].items()},'contract':sha(raw(CONTRACT)),'lineage':sha(raw({'graph':BASE['graph'],'columns':BASE['column_lineage']})),'producer':sha((ROOT/'engine.py').read_bytes())}
    output=[{'category':'c1','amount_sum':100,'class':'public','product_rows':[1]},{'category':'c2','amount_sum':0,'class':'internal','product_rows':[2]}]
    cache={'bindings':bindings,'output':output,'output_digest':sha(raw(output))}
    q=copy.deepcopy(BASE);q['cache']=cache;cases['same-source-cache']=q
    q=copy.deepcopy(q);q['sources']['products'][0]['amount']=101;cases['source-change']=q
    return cases

def record():
    ident=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder=ROOT/'observations'/ident;folder.mkdir(parents=True);started=now();runs=[]
    for key,request in fixtures().items():
        case=folder/key;case.mkdir();write(case/'input.json',request);stdin=json.dumps(request,ensure_ascii=False);began=now()
        p=subprocess.run([sys.executable,'engine.py',str((case/'result.json').relative_to(ROOT))],cwd=ROOT,input=stdin,text=True,capture_output=True)
        command={'argv':['python3','engine.py',str((case/'result.json').relative_to(ROOT))],'started_at':began,'completed_at':now(),'stdin':stdin,'stdout':p.stdout,'stderr':p.stderr,'exit_code':p.returncode}
        for s in ('stdin','stdout','stderr'):command[s+'_digest']=sha(command[s].encode())
        write(case/'command.json',command);write(case/'trace.json',[json.loads(line) for line in p.stdout.splitlines()]);runs.append({'id':key,'exit_code':p.returncode})
    names=['engine.py','runner.py','checker.py','test_negative.py','index.html','preview.py','README.md','sources.json','coverage.json','skills/atlas-data-governance-quality-lineage/SKILL.md','skills/atlas-data-governance-quality-lineage/route.py']
    write(folder/'observation.json',{'execution_id':ident,'started_at':started,'completed_at':now(),'environment':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine()},'source_bindings':{n:sha((ROOT/n).read_bytes()) for n in names},'runs':runs,'real_data':False,'PII':False,'company_policy_certification':False,'external_services':0})
    began=now();p=subprocess.run([sys.executable,'checker.py','--oracle',str(folder.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True)
    if p.returncode:raise RuntimeError(p.stderr)
    write(folder/'oracle.json',json.loads(p.stdout));write(folder/'oracle-command.json',{'argv':['python3','checker.py','--oracle',str(folder.relative_to(ROOT))],'started_at':began,'completed_at':now(),'stdout':p.stdout,'stderr':p.stderr,'exit_code':p.returncode,'stdout_digest':sha(p.stdout.encode()),'stderr_digest':sha(p.stderr.encode())})
    write(folder/'artifact-index.json',{p.relative_to(folder).as_posix():{'digest':sha(p.read_bytes()),'size':p.stat().st_size} for p in folder.rglob('*') if p.is_file()});write(ROOT/'current.json',{'directory':str(folder.relative_to(ROOT))});print(json.dumps({'directory':str(folder.relative_to(ROOT)),'cases':len(runs)}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');args=p.parse_args()
    if args.record:record()
    else:raise SystemExit(subprocess.call([sys.executable,str(ROOT/'checker.py')]))
