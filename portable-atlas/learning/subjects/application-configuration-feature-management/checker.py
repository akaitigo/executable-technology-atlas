"""Read-only fixed configuration/provenance/error/hash-bucket hand oracle."""
import argparse,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
D={'timeout_ms':1000,'retries':2,'flag_enabled':True,'rollout_percent':50}
ACTORS=['alpha','beta','gamma','delta']
HASHES={'alpha':'56e7a93697b573bf4b8f432aee27e7e31cc5543652ca711599183c5d65fb1c01','beta':'91f90af63a205512f8ace165338891e076f660dbb8997763b13588c479850677','gamma':'e06cc08a6e215fdca3069f05f9928d3774e7f46584793cf0c7e56423d564f7e3','delta':'94ea556c5c0921cc484f21bfacee68179e78dfe83e5281915f72866ec0c0355e'}
BUCKETS={'alpha':2710,'beta':7590,'gamma':3562,'delta':5260}
INPUTS={
'defaults':{},'env-overrides':{'env':{'APP_TIMEOUT_MS':'2000','APP_FLAG_ENABLED':'false','APP_ROLLOUT_PERCENT':'25'}},
 'task-over-env':{'env':{'APP_TIMEOUT_MS':'2000','APP_FLAG_ENABLED':'false'},'task':{'timeout_ms':3000,'flag_enabled':True,'rollout_percent':75,'retries':5}},
 'strict-false':{'env':{'APP_FLAG_ENABLED':'false'},'task':{'rollout_percent':100}},
 'truthiness-bug':{'mode':'truthiness-bug','env':{'APP_FLAG_ENABLED':'false'},'task':{'rollout_percent':100}},
 'zero-rollout':{'task':{'rollout_percent':0}},'full-rollout':{'task':{'rollout_percent':100}},'stable-repeat':{'actors':['alpha','beta','gamma','delta','alpha']},
 'invalid-env-bool':{'env':{'APP_FLAG_ENABLED':'TRUE'}},'invalid-env-int':{'env':{'APP_TIMEOUT_MS':'oops'}},
 'invalid-timeout-range':{'task':{'timeout_ms':0}},'invalid-rollout-range':{'task':{'rollout_percent':101}},'bool-as-integer':{'task':{'retries':True}},
 'unknown-secret-field':{'task':{'api_key':'EXAMPLE_NOT_A_SECRET'}},'unknown-env-field':{'env':{'APP_SECRET':'EXAMPLE_NOT_A_SECRET'}},'task-string-false':{'task':{'flag_enabled':'false'}},
 'lower-config-boundary':{'task':{'timeout_ms':1,'retries':0,'rollout_percent':0}},'upper-config-boundary':{'task':{'timeout_ms':5000,'retries':5,'rollout_percent':100}}}
# Explicit raw->typed hand table, not an env parser.
E=[('env-input','APP_TIMEOUT_MS','timeout_ms','2000',2000),('env-input','APP_FLAG_ENABLED','flag_enabled','false',False)]
F=[('env-input','APP_FLAG_ENABLED','flag_enabled','false',False),('task-json','rollout_percent','rollout_percent',100,100)]
HAND={'env-overrides':E+[('env-input','APP_ROLLOUT_PERCENT','rollout_percent','25',25)],'task-over-env':E+[('task-json','timeout_ms','timeout_ms',3000,3000),('task-json','flag_enabled','flag_enabled',True,True),('task-json','rollout_percent','rollout_percent',75,75),('task-json','retries','retries',5,5)],'strict-false':F,'truthiness-bug':[('env-input','APP_FLAG_ENABLED','flag_enabled','false',True),F[1]],'zero-rollout':[('task-json','rollout_percent','rollout_percent',0,0)],'full-rollout':[F[1]],'lower-config-boundary':[('task-json','timeout_ms','timeout_ms',1,1),('task-json','retries','retries',0,0),('task-json','rollout_percent','rollout_percent',0,0)],'upper-config-boundary':[('task-json','timeout_ms','timeout_ms',5000,5000),('task-json','retries','retries',5,5),F[1]]}
ERRORS={'invalid-env-bool':('env-input','APP_FLAG_ENABLED','strict-boolean-required'),'invalid-env-int':('env-input','APP_TIMEOUT_MS','integer-string-required'),'invalid-timeout-range':('task-json','timeout_ms','range'),'invalid-rollout-range':('task-json','rollout_percent','range'),'bool-as-integer':('task-json','retries','integer-required'),'unknown-secret-field':('task-json','api_key','unknown-field'),'unknown-env-field':('env-input','APP_SECRET','unknown-field'),'task-string-false':('task-json','flag_enabled','boolean-required')}
ON={'defaults':{'alpha','gamma'},'stable-repeat':{'alpha','gamma'},'task-over-env':{'alpha','gamma','delta'},'truthiness-bug':set(ACTORS),'full-rollout':set(ACTORS),'upper-config-boundary':set(ACTORS)}
def raw(v):return (json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode()
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text())
def oracle(folder):
    obs=read(folder/'observation.json');assert {r['id'] for r in obs['runs']}==set(INPUTS) and len(obs['runs'])==18,'case set';reports=[]
    for run in obs['runs']:
        key=run['id'];case=folder/key;request=read(case/'input.json');result=read(case/'result.json');command=read(case/'command.json');trace=read(case/'trace.json');expected={'mode':'strict','env':{},'task':{},'actors':ACTORS}|INPUTS[key]
        assert request==expected,'hand input';assert json.loads(command['stdin'])==request and command['stderr']=='','raw input/stderr'
        for s in ('stdin','stdout','stderr'):assert sha(command[s].encode())==command[s+'_digest'],'raw stream digest'
        assert trace==[json.loads(line) for line in command['stdout'].splitlines()],'raw trace'
        config=dict(D);provenance={k:{'layer':'default','raw':v,'typed':v} for k,v in D.items()};overrides=[]
        for layer,source,field,value,typed in HAND.get(key,[]):
            overrides.append({'layer':layer,'source_field':source,'field':field,'raw':value,'typed':typed,'prior':config[field]});config[field]=typed;provenance[field]={'layer':layer,'raw':value,'typed':typed}
        errors=[]
        if key in ERRORS:layer,field,reason=ERRORS[key];errors=[{'layer':layer,'field':field,'reason':reason}]
        decision='refused' if errors else 'accepted';exit_code=2 if errors else 0
        assert result['decision']==decision and result['exit_code']==command['exit_code']==run['exit_code']==exit_code,'hand decision'
        assert result['mode']==request['mode'] and result['errors']==errors,'hand errors'
        assert result['config']==(None if errors else config),'hand configuration'
        assert result['provenance']==({} if errors else provenance),'hand provenance'
        assert result['overrides']==overrides,'hand override history'
        actors=[]
        if not errors:
            for a in request['actors']:
                enabled=a in ON.get(key,set());actors.append({'actor':a,'hash':HASHES[a],'prefix_integer':int(HASHES[a][:8],16),'bucket':BUCKETS[a],'threshold':config['rollout_percent']*100,'enabled':enabled,'reason':'master-disabled' if not config['flag_enabled'] else 'in-rollout' if enabled else 'outside-rollout'})
        assert result['actors']==actors,'fixed actor hash/bucket/decision differs'
        bindings={'input_digest':sha(raw(expected)),'producer_digest':obs['source_bindings']['evaluator.py'],'defaults_digest':sha(raw(D))};assert result['bindings']==bindings,'input/source binding'
        stages=[{'event':'defaults-loaded','config':D,'bindings':bindings}]+[{'event':'override-applied',**o} for o in overrides]
        if errors:stages += [{'event':'refused-field',**e} for e in errors]+[{'event':'configuration-refused','errors':errors}]
        else:stages += [{'event':'configuration-resolved','config':config,'provenance':provenance}]+[{'event':'flag-evaluated',**a} for a in actors]+[{'event':'accepted','enabled_count':sum(a['enabled'] for a in actors)}]
        assert trace==stages,'hand stage trace'
        reports.append({'id':key,'decision':decision,'exit_code':exit_code,'config':None if errors else config,'provenance':{} if errors else provenance,'overrides':overrides,'errors':errors,'actors':actors,'enabled_count':sum(a['enabled'] for a in actors),'bindings':bindings,'mode':request['mode']})
    return {'passed':True,'cases':18,'independence':'Fixed raw->typed, error, actor SHA256 and bucket table; imports no evaluator/runner','rollout_algorithm':'SHA256 UTF8 demo-v1 + NUL + actor; first8hex mod10000; bucket < percent*100 and master enabled','reports':reports}
def check():
    folder=ROOT/read(ROOT/'current.json')['directory'];obs=read(folder/'observation.json')
    for n,d in obs['source_bindings'].items():assert sha((ROOT/n).read_bytes())==d,'stale source '+n
    index=read(folder/'artifact-index.json');assert set(index)=={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file() and p.name!='artifact-index.json'},'artifact set'
    for n,e in index.items():
        b=(folder/n).read_bytes();assert e=={'digest':sha(b),'size':len(b)},'artifact digest '+n
    assert oracle(folder)==read(folder/'oracle.json'),'saved oracle differs';print(json.dumps({'passed':True,'cases':18,'read_only':True}))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--oracle');args=p.parse_args()
    try:
        if args.oracle:
            assert re.fullmatch(r'(observations/[0-9TZ]+|oracle-negative-[a-zA-Z0-9_-]+)',args.oracle),'oracle path';print(json.dumps(oracle(ROOT/args.oracle),ensure_ascii=False))
        else:check()
    except (AssertionError,KeyError,ValueError,OSError) as exc:print(str(exc),file=sys.stderr);raise SystemExit(1)
