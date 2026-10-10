"""Task-owned file-byte revisions and in-memory actual state. Not Git/Argo/cluster."""
import copy
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
FIELDS=('image','replicas','note')
CASES=('desired-change','drift-restore','observe-only','stale-revision','rollback','ignore-note','manage-note','tampered-bytes','invalid-ignore','invalid-state')

def sha(raw): return hashlib.sha256(raw).hexdigest()
def digest(value): return sha(json.dumps(value,sort_keys=True,separators=(',',':')).encode())
def validate_state(state):
    if not isinstance(state,dict) or set(state)!=set(FIELDS): raise ValueError('invalid-state')
    if state['image'] not in ('demo:v1','demo:v2','demo:manual') or type(state['replicas']) is not int or not 0<=state['replicas']<=5 or state['note'] not in ('declared','operator'):
        raise ValueError('invalid-state')
def packet(name):
    manifest=json.loads((ROOT/'manifest.json').read_text())
    m=manifest[name]
    raw=(ROOT/m['file']).read_bytes()
    return {'name':name,'generation':m['generation'],'sha256':m['sha256'],'bytes':raw.decode()}
def revision(p): return {'generation':p['generation'],'sha256':p['sha256']}

def reconcile(live,p,authoritative,mode='apply',ignore=()):
    before=copy.deepcopy(live)
    result={'liveBefore':before,'packet':copy.deepcopy(p),'authoritative':revision(authoritative),'mode':mode,'ignore':list(ignore)}
    try:
        validate_state(live)
        if mode not in ('apply','observe'): raise ValueError('invalid-mode')
        if not isinstance(ignore,(tuple,list)) or len(set(ignore))!=len(ignore) or any(k!='note' for k in ignore): raise ValueError('invalid-ignore')
        if revision(p)!=revision(authoritative): raise ValueError('stale-revision')
        if sha(p['bytes'].encode())!=p['sha256']: raise ValueError('bytes-hash-mismatch')
        desired=json.loads(p['bytes']);validate_state(desired)
    except (ValueError,KeyError,TypeError) as e:
        result.update(action='refuse',reason=str(e),liveAfter=before,diff=[],ignoredDiff=[])
        return result
    differences=[{'field':k,'live':live[k],'desired':desired[k]} for k in FIELDS if live[k]!=desired[k]]
    managed=[d for d in differences if d['field'] not in ignore]
    ignored=[d for d in differences if d['field'] in ignore]
    after=copy.deepcopy(live)
    if mode=='apply':
        for d in managed: after[d['field']]=d['desired']
    action='apply' if mode=='apply' and managed else 'observe' if mode=='observe' and managed else 'in-sync'
    result.update(action=action,desired=desired,diff=managed,ignoredDiff=ignored,liveAfter=after)
    result['managedEqualAfter']=all(after[k]==desired[k] for k in FIELDS if k not in ignore)
    result['exactEqualAfter']=after==desired
    result['beforeHash']=digest(before);result['afterHash']=digest(after)
    return result

def run(case='desired-change'):
    if case not in CASES: raise ValueError('unsupported-case')
    live=json.loads(packet('v1')['bytes']);current=packet('v1');trace=[]
    def tick(p=None,mode='apply',ignore=()):
        nonlocal live
        row=reconcile(live,p or current,current,mode,ignore);live=copy.deepcopy(row['liveAfter']);row['event']='tick';trace.append(row)
    def publish(name):
        nonlocal current
        new=packet(name)
        if new['generation']<=current['generation']: raise ValueError('non-increasing-publication')
        current=new;trace.append({'event':'publish','packet':copy.deepcopy(current),'liveAfter':copy.deepcopy(live),'action':'new-desired'})
    def manual(changes):
        nonlocal live
        before=copy.deepcopy(live);live.update(changes);trace.append({'event':'manual-drift','changes':changes,'liveBefore':before,'liveAfter':copy.deepcopy(live),'action':'manual'})
    tick();publish('v2')
    if case=='desired-change': tick();tick()
    elif case in ('drift-restore','observe-only'):
        tick();manual({'image':'demo:manual','replicas':5});tick(mode='observe' if case=='observe-only' else 'apply');tick(mode='observe' if case=='observe-only' else 'apply')
    elif case=='stale-revision': tick(packet('v1'));tick()
    elif case=='rollback': tick();publish('rollback-v3');tick();tick()
    elif case in ('ignore-note','manage-note'):
        manual({'note':'operator'});tick(ignore=['note'] if case=='ignore-note' else []);tick(ignore=['note'] if case=='ignore-note' else [])
    elif case=='tampered-bytes':
        p=copy.deepcopy(current);p['bytes']=p['bytes'].replace('demo:v2','demo:v1');tick(p)
    elif case=='invalid-ignore': tick(ignore=['image'])
    elif case=='invalid-state': manual({'replicas':-1});tick()
    return {'case':case,'model':'local file bytes + in-memory reconcile, not Git/Argo product/cluster execution','trace':trace,'final':live,'finalHash':digest(live),'latestRevision':revision(current)}
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--case',choices=CASES,default=CASES[0]);a=p.parse_args();print(json.dumps(run(a.case),ensure_ascii=False,indent=2))
