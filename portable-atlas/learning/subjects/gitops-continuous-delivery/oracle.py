"""Independent fixed transition table. No runner import or file parsing."""
import hashlib,json
V1={'image':'demo:v1','replicas':2,'note':'declared'}
V2={'image':'demo:v2','replicas':3,'note':'declared'}
MANUAL={'image':'demo:manual','replicas':5,'note':'declared'}
IGNORED={'image':'demo:v2','replicas':3,'note':'operator'}
BAD={'image':'demo:v1','replicas':-1,'note':'declared'}
EXPECTED={
 'desired-change':(['in-sync','new-desired','apply','in-sync'],V2),
 'drift-restore':(['in-sync','new-desired','apply','manual','apply','in-sync'],V2),
 'observe-only':(['in-sync','new-desired','apply','manual','observe','observe'],MANUAL),
 'stale-revision':(['in-sync','new-desired','refuse','apply'],V2),
 'rollback':(['in-sync','new-desired','apply','new-desired','apply','in-sync'],V1),
 'ignore-note':(['in-sync','new-desired','manual','apply','in-sync'],IGNORED),
 'manage-note':(['in-sync','new-desired','manual','apply','in-sync'],V2),
 'tampered-bytes':(['in-sync','new-desired','refuse'],V1),
 'invalid-ignore':(['in-sync','new-desired','refuse'],V1),
 'invalid-state':(['in-sync','new-desired','manual','refuse'],BAD)
}
HASHES={'v1':'4a6cff29d2f03c080d14d648cb5fadf9986c669911a3cfd8a8f3a6702cd573fe','v2':'a61061f23fe448b173e7ebbb99735c96437f1001631aee0af30ab733228b449a','rollback-v3':'4a6cff29d2f03c080d14d648cb5fadf9986c669911a3cfd8a8f3a6702cd573fe'}
def statehash(state):
    # Independent construction of canonical field ordering; fixed ASCII model.
    raw='{"image":'+json.dumps(state['image'])+',"note":'+json.dumps(state['note'])+',"replicas":'+str(state['replicas'])+'}'
    return hashlib.sha256(raw.encode()).hexdigest()
def transition(live,name,mode,ignore):
    if mode=='observe': return dict(live)
    desired=dict(V2 if name=='v2' else V1)
    if ignore: desired['note']=live['note']
    return desired
