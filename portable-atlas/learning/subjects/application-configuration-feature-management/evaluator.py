"""Fictional cloud configuration model. Reads JSON stdin, never os.environ."""
import hashlib,json,re,sys
from pathlib import Path
DEFAULTS={'timeout_ms':1000,'retries':2,'flag_enabled':True,'rollout_percent':50}
ENV={'APP_TIMEOUT_MS':'timeout_ms','APP_RETRIES':'retries','APP_FLAG_ENABLED':'flag_enabled','APP_ROLLOUT_PERCENT':'rollout_percent'}
RANGES={'timeout_ms':[1,5000],'retries':[0,5],'rollout_percent':[0,100]}
SALT='demo-v1'
def raw(v):return (json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode()
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def emit(event,**fields):print(json.dumps({'event':event,**fields},ensure_ascii=False),flush=True)
def evaluate(request):
    mode=request['mode'];errors=[];overrides=[];config=dict(DEFAULTS);provenance={k:{'layer':'default','raw':v,'typed':v} for k,v in DEFAULTS.items()}
    bindings={'input_digest':sha(raw(request)),'producer_digest':sha(Path(__file__).read_bytes()),'defaults_digest':sha(raw(DEFAULTS))}
    emit('defaults-loaded',config=DEFAULTS,bindings=bindings)
    if mode not in ('strict','truthiness-bug'):errors.append({'layer':'request','field':'mode','reason':'unsupported-mode'})
    for layer,values in [('env-input',request['env']),('task-json',request['task'])]:
        for source,value in values.items():
            key=ENV.get(source) if layer=='env-input' else source if source in DEFAULTS else None
            if key is None:
                error={'layer':layer,'field':source,'reason':'unknown-field'};errors.append(error);emit('refused-field',**error);continue
            try:
                typed=value
                if layer=='env-input':
                    if type(value) is not str:raise ValueError('env-string-required')
                    if key=='flag_enabled':
                        if mode=='truthiness-bug':typed=bool(value)
                        elif value in ('true','false'):typed=value=='true'
                        else:raise ValueError('strict-boolean-required')
                    else:
                        if not re.fullmatch(r'-?(?:0|[1-9][0-9]*)',value):raise ValueError('integer-string-required')
                        typed=int(value)
                if key=='flag_enabled' and type(typed) is not bool:raise ValueError('boolean-required')
                if key in RANGES:
                    if type(typed) is not int:raise ValueError('integer-required')
                    low,high=RANGES[key]
                    if not low<=typed<=high:raise ValueError('range')
                prior=config[key];config[key]=typed;provenance[key]={'layer':layer,'raw':value,'typed':typed};item={'layer':layer,'source_field':source,'field':key,'raw':value,'typed':typed,'prior':prior};overrides.append(item);emit('override-applied',**item)
            except ValueError as exc:
                error={'layer':layer,'field':source,'reason':str(exc)};errors.append(error);emit('refused-field',**error)
    if errors:
        emit('configuration-refused',errors=errors);return {'decision':'refused','exit_code':2,'mode':mode,'config':None,'provenance':{},'overrides':overrides,'errors':errors,'actors':[],'bindings':bindings}
    emit('configuration-resolved',config=config,provenance=provenance)
    actors=[]
    for actor in request['actors']:
        digest=hashlib.sha256((SALT+'\0'+actor).encode()).hexdigest();prefix=int(digest[:8],16);bucket=prefix%10000;threshold=config['rollout_percent']*100;enabled=config['flag_enabled'] and bucket<threshold
        item={'actor':actor,'hash':digest,'prefix_integer':prefix,'bucket':bucket,'threshold':threshold,'enabled':enabled,'reason':'master-disabled' if not config['flag_enabled'] else 'in-rollout' if enabled else 'outside-rollout'};actors.append(item);emit('flag-evaluated',**item)
    emit('accepted',enabled_count=sum(a['enabled'] for a in actors));return {'decision':'accepted','exit_code':0,'mode':mode,'config':config,'provenance':provenance,'overrides':overrides,'errors':[],'actors':actors,'bindings':bindings}
if __name__=='__main__':
    result=evaluate(json.load(sys.stdin));Path(sys.argv[1]).write_bytes(raw(result));raise SystemExit(result['exit_code'])
