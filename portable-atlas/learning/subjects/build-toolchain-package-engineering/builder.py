"""Two-action local toy build; actual input/output bytes and local action cache/CAS."""
import hashlib,json,os,re,sys
from graphlib import TopologicalSorter,CycleError
from pathlib import Path

def raw(v):return (json.dumps(v,sort_keys=True,ensure_ascii=False,separators=(',',':'))+'\n').encode()
def sha(b):return 'sha256:'+hashlib.sha256(b).hexdigest()
def emit(event,**fields):print(json.dumps({'event':event,**fields},ensure_ascii=False),flush=True)
def build(work,request):
    graph=request['graph'];mode=request['mode'];tool=request['toolchain'];errors=[]
    if mode not in ('content','mtime-only') or tool not in ('toy-1','toy-2'):errors.append({'kind':'unsupported-config'})
    for node,spec in graph.items():
        if not re.fullmatch(r'[a-z][a-z0-9.-]*',node) or spec['action'] not in ('compile','package'):errors.append({'kind':'unsupported-action','node':node})
        if len(spec['deps'])!=2:errors.append({'kind':'arity','node':node})
        for dep in spec['deps']:
            if not re.fullmatch(r'[a-z][a-z0-9.-]*',dep) or (dep not in graph and not (work/'inputs'/dep).is_file()):errors.append({'kind':'missing-dependency','node':node,'dependency':dep})
    if errors:emit('refused',errors=errors);return {'decision':'refused','exit_code':2,'errors':errors,'order':[],'actions':[]}
    try:order=list(TopologicalSorter({n:[d for d in s['deps'] if d in graph] for n,s in graph.items()}).static_order())
    except CycleError:
        errors=[{'kind':'cycle'}];emit('refused',errors=errors);return {'decision':'refused','exit_code':2,'errors':errors,'order':[],'actions':[]}
    emit('graph-accepted',order=order)
    out=work/'outputs';out.mkdir(exist_ok=True);ac=work/'cache'/'actions';cas=work/'cache'/'blobs';ac.mkdir(parents=True,exist_ok=True);cas.mkdir(exist_ok=True);actions=[]
    for node in order:
        spec=graph[node];deps={d:(out/d if d in graph else work/'inputs'/d) for d in spec['deps']};bindings={d:{'digest':sha(p.read_bytes()),'size':p.stat().st_size,'mtime_ns':p.stat().st_mtime_ns} for d,p in deps.items()}
        payload={'mode':mode,'action':spec['action'],'dependencies':spec['deps'],'toolchain':tool,'builder_digest':sha(Path(__file__).read_bytes()),'inputs':{d:bindings[d]['digest'] if mode=='content' else bindings[d]['mtime_ns'] for d in spec['deps']}}
        key=sha(raw(payload));entry=ac/(key[7:]+'.json');state='hit' if entry.exists() else 'miss'
        if state=='hit':
            meta=json.loads(entry.read_text());blob=cas/(meta['output_digest'][7:]+'.bin');produced=blob.read_bytes()
            if sha(produced)!=meta['output_digest'] or len(produced)!=meta['size']:raise ValueError('cache-integrity')
        else:
            values=[deps[d].read_bytes() for d in spec['deps']]
            produced=(b'object:'+tool.encode()+b'\n'+values[0].upper()+values[1]) if spec['action']=='compile' else values[0]+values[1]
            digest=sha(produced);(cas/(digest[7:]+'.bin')).write_bytes(produced);entry.write_bytes(raw({'key':key,'payload':payload,'output_digest':digest,'size':len(produced)}))
        target=out/node;target.write_bytes(produced);stamp=max(p.stat().st_mtime_ns for p in deps.values());os.utime(target,ns=(stamp,stamp))
        item={'node':node,'action':spec['action'],'cache':state,'key':key,'key_payload':payload,'input_bindings':bindings,'output_digest':sha(produced),'output_size':len(produced),'output_hex':produced.hex(),'output_mtime_ns':target.stat().st_mtime_ns};actions.append(item);emit('action',**item)
    emit('built',hits=sum(a['cache']=='hit' for a in actions),misses=sum(a['cache']=='miss' for a in actions));return {'decision':'built','exit_code':0,'errors':[],'order':order,'actions':actions}
if __name__=='__main__':
    result=build(Path(sys.argv[1]),json.load(sys.stdin));Path(sys.argv[2]).write_bytes(raw(result));raise SystemExit(result['exit_code'])
