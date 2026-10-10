import sys
sys.dont_write_bytecode=True
import argparse,ast,datetime,hashlib,itertools,json,re
from pathlib import Path
import model,oracle
ROOT=Path(__file__).resolve().parent
SHA=lambda b:hashlib.sha256(b).hexdigest()
def measurements(bootstrap=False):
    f=json.loads((ROOT/'fixtures.json').read_text());assert f['principals']==oracle.ACTORS and f['inode']=={'ownerUid':1001,'ownerGid':2001}
    operations=[('read','file'),('write','file'),('execute','file'),('search','directory'),('read-write','file')];grid=[];differ=0
    for digits,principal,(op,kind) in itertools.product(itertools.product('01234567',repeat=3),oracle.CLASS,operations):
        mode=''.join(digits);d=model.experiment(mode,principal,op,kind);e=oracle.expected(mode,principal,op,kind);a=d['protected']
        assert {k:a[k] for k in ('status','selected','allowed')}=={k:e[k] for k in ('status','selected','allowed')},(mode,principal,op)
        weights={'r':4,'w':2,'x':1};assert a['selectedBits']==sum(weights[r] for r in e['rights']) and a['requestMask']==sum(weights[r] for r in e['needs'])
        assert a['fallback'] is False and d['filesChanged'] is False and d['kernelObserved'] is False
        assert d['inputSha256']==model.digest(d['input']) and d['traceSha256']==model.digest({'protected':a['trace'],'bad':d['bad']['trace']})
        trace=a['trace'];assert len(trace)==3 and trace[1]['selected']==e['selected'] and trace[2]['allowed']==e['allowed']
        assert trace[0]['nineBits']==''.join(format(int(digit),'03b') for digit in mode)
        assert trace[0]['decimal']==sum(int(v)*power for v,power in zip(mode,(64,8,1)))
        differs=a['allowed']!=d['bad']['allowed'];differ+=differs
        grid.append({'mode':mode,'principal':principal,'operation':op,'kind':kind,'inputSha256':d['inputSha256'],'traceSha256':d['traceSha256'],'selected':a['selected'],'selectedBits':a['selectedBits'],'requestMask':a['requestMask'],'allowed':a['allowed'],'badAllowed':d['bad']['allowed'],'expected':e})
    hands=[('004','owner','read','file','owner',False,True),('004','other','read','file','other',True,True),('040','group','read','file','group',True,True),('040','supplementary','read','file','group',True,True),('400','other','read','file','other',False,True),('044','owner-group','read','file','owner',False,True),('400','owner','read-write','file','owner',False,False),('001','other','search','directory','other',True,True)]
    hand=[]
    for mode,principal,op,kind,selected,allowed,bad in hands:
        d=model.experiment(mode,principal,op,kind);assert (d['protected']['selected'],d['protected']['allowed'],d['bad']['allowed'])==(selected,allowed,bad);hand.append({'actual':d,'expected':oracle.expected(mode,principal,op,kind)})
    valid={'mode':'004','inode':f['inode'],'actor':f['principals']['owner'],'operation':'read','kind':'file','security':'none'};reject=[]
    patches=[{'mode':v} for v in ('','4','0000','888','-01','0755','1777',None,True,4)]+[{'security':v} for v in ('acl','capabilities','lsm','fsuid-override')]+[{'actor':f['principals']['root']},{'operation':'delete'},{'kind':'symlink'},{'operation':'search','kind':'file'},{'operation':'execute','kind':'directory'},{'actor':{'uid':True,'gid':1,'supplementary':[]}},{'actor':{'uid':65536,'gid':1,'supplementary':[]}},{'actor':{'uid':-1,'gid':1,'supplementary':[]}},{'actor':{'uid':1,'gid':1,'supplementary':[1,2,3,4]}},{'actor':{'uid':1,'gid':1,'supplementary':[True]}},{'actor':{'uid':1,'gid':1,'supplementary':'x'}},{'inode':{}},{'actor':{}},{'inode':{'ownerUid':-1,'ownerGid':2}}]
    for patch in patches:
        args={**valid,**patch};d=model.decide(**args);assert d['protected']['status']=='rejected' and d['protected']['allowed'] is None and not d['protected']['trace'];reject.append(d)
    for mode in ('000','777'):
        for principal in oracle.CLASS:
            d=model.experiment(mode,principal,'read-write');assert d['protected']['allowed']==(mode=='777')
    for uid in (1,65535):
        d=model.decide('400',{'ownerUid':uid,'ownerGid':0},{'uid':uid,'gid':0,'supplementary':[0,65535,0]});assert d['protected']['allowed']
    faults=[]
    d=model.experiment();assert not d['protected']['allowed'] and d['bad']['allowed'];faults.append({'fault':'any-class union','actual':d,'faulty':True,'expected':False})
    d=model.experiment('400','owner','read-write');wrong=bool(d['protected']['selectedBits']&d['protected']['requestMask']);assert wrong and not d['protected']['allowed'];faults.append({'fault':'any requested bit instead of all','actual':d,'faulty':wrong,'expected':False})
    d=model.experiment('040','supplementary');wrong=model.experiment('040','other')['protected']['allowed'];assert not wrong and d['protected']['allowed'];faults.append({'fault':'ignoring supplementary groups','actual':d,'faulty':wrong,'expected':True})
    d=model.experiment('044','owner-group');wrong=model.experiment('044','group')['protected']['allowed'];assert wrong and not d['protected']['allowed'];faults.append({'fault':'group before owner','actual':d,'faulty':wrong,'expected':False})
    tree=ast.parse((ROOT/'model.py').read_text());names={n.id for n in ast.walk(tree) if isinstance(n,ast.Name)};attrs={n.attr for n in ast.walk(tree) if isinstance(n,ast.Attribute)};assert not names.intersection({'os','subprocess','exec','eval'}) and not attrs.intersection({'chmod','chown','access','stat','setuid','setgid'})
    for filename in ('README.md','index.html'):
        text=(ROOT/filename).read_text();assert all(url in text for url in model.SOURCES.values());assert '未教材' in text and 'supplementary' in text and 'Linux' in text
        for url in ('https://man7.org/linux/man-pages/man2/clone.2.html','https://man7.org/linux/man-pages/man7/namespaces.7.html','https://docs.kernel.org/filesystems/proc.html'):assert url in text
    for link in re.findall(r'\]\(([^)#]+)(?:#[^)]*)?\)',(ROOT/'README.md').read_text()):
        if link.startswith('http'):continue
        if bootstrap and link in ('evidence/run.json','evidence/bindings.json','evidence/ui-qa.json','evidence/routing-smoke.json'):continue
        assert (ROOT/link).is_file(),link
    return {'gridCount':len(grid),'disagreementCount':differ,'handCount':len(hand),'rejectCount':len(reject),'faultCount':len(faults),'grid':grid,'hand':hand,'rejections':reject,'faults':faults,'sources':model.SOURCES}
def bindings():return {str(p.relative_to(ROOT)):SHA(p.read_bytes()) for p in sorted(ROOT.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='bindings.json'}
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();m=measurements(a.record)
    if a.record:
        (ROOT/'evidence/run.json').write_text(json.dumps({'recordedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':{'python':sys.version.split()[0],'platform':sys.platform,'linuxKernelRun':False},'measurements':m},ensure_ascii=False,indent=2)+'\n')
        (ROOT/'evidence/bindings.json').write_text(json.dumps({'sources':model.SOURCES,'files':bindings()},indent=2)+'\n')
    else:
        assert json.loads((ROOT/'evidence/run.json').read_text())['measurements']==m
        assert json.loads((ROOT/'evidence/bindings.json').read_text())=={'sources':model.SOURCES,'files':bindings()}
        qa=json.loads((ROOT/'evidence/ui-qa.json').read_text());assert qa['serverStopped'] and qa['tabClosed'] and len(qa['cases'])==10
        for row in qa['cases']:
            d=model.experiment(*row['args']);assert row['inputSha256']==d['inputSha256'] and row['traceSha256']==d['traceSha256']
            assert row['status']==d['protected']['status'] and row['selected']==d['protected']['selected'] and row['allowed']==d['protected']['allowed'] and row['badAllowed']==d['bad']['allowed']
        assert json.loads((ROOT/'evidence/routing-smoke.json').read_text())['forwardAgentEval']=='not-run'
    print(json.dumps({k:v for k,v in m.items() if k not in ('grid','hand','rejections','faults')},ensure_ascii=False))
if __name__=='__main__':main()
