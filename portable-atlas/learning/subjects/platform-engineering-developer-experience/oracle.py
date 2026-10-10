"""Independent literal expected files: no runner/template/contract import."""
import hashlib,datetime
CEDAR={'README.md':'# cedar\n\nOwner: team-a\nKind: library\n','RUNBOOK.md':'# cedar local fixture\n\nOwner: team-a\nNo service is deployed.\n','project.json':'{"name":"cedar","owner":"team-a","kind":"library","schemaVersion":2,"templateVersion":2}\n','src/main.py':'PROJECT = "cedar"\nKIND = "library"\n'}
MAPLE={'README.md':'# maple\n\nOwner: team-b\nKind: worker\n','RUNBOOK.md':'# maple local fixture\n\nOwner: team-b\nNo service is deployed.\n','project.json':'{"name":"maple","owner":"team-b","kind":"worker","schemaVersion":2,"templateVersion":2}\n','src/main.py':'PROJECT = "maple"\nKIND = "worker"\n'}
ONE={'README.md':'# a\n\nOwner: team-a\nKind: library\n','RUNBOOK.md':'# a local fixture\n\nOwner: team-a\nNo service is deployed.\n','project.json':'{"name":"a","owner":"team-a","kind":"library","schemaVersion":2,"templateVersion":2}\n','src/main.py':'PROJECT = "a"\nKIND = "library"\n'}
DIFF={'old-template':(['RUNBOOK.md'],[],['project.json'],['templateVersion']),'schema-drift':([],[],['project.json'],['schemaVersion']),'tampered-file':([],[],['README.md'],[]),'missing-file':(['src/main.py'],[],[],[]),'extra-file':([],['extra.txt'],[],[])}
def hashes(t):return {k:hashlib.sha256(v.encode()).hexdigest() for k,v in sorted(t.items())}
def expected(case):
    t=dict(MAPLE if case in ('maple','tampered-file') else ONE if case=='one-letter' else CEDAR)
    if case=='old-template':t.pop('RUNBOOK.md');t['project.json']='{"name":"cedar","owner":"team-a","kind":"library","schemaVersion":2,"templateVersion":1}\n'
    elif case=='schema-drift':t['project.json']='{"name":"cedar","owner":"team-a","kind":"library","schemaVersion":1,"templateVersion":2}\n'
    elif case=='tampered-file':t['README.md']='# maple\n\nOwner: team-b\nKind: worker\nDRIFT\n'
    elif case=='missing-file':t.pop('src/main.py')
    elif case=='extra-file':t['extra.txt']='unexpected\n'
    return t
def audit(r):
    case=r['case'];reject=case in ('invalid-config','path-escape')
    if reject:assert r['status']=='rejected' and r['reason']==('config-keys' if case=='invalid-config' else 'path-escape') and r['tree']==r['repeatTree']=={} and r['filesWritten']==0
    else:
        standard=MAPLE if case in ('maple','tampered-file') else ONE if case=='one-letter' else CEDAR;actual=expected(case);repeat=expected('old-template') if case=='old-template' else standard
        assert r['tree']==actual and r['repeatTree']==repeat and r['deterministicRender'] and r['preFaultFileHashes']==r['repeatFileHashes']==hashes(repeat)
        p=r['report'];assert p['expectedFileHashes']==hashes(standard) and p['actualFileHashes']==hashes(actual)
        m,e,c,d=DIFF.get(case,([],[],[],[]));assert [p[k] for k in ('missing','extra','changed','metadataDrift')]==[m,e,c,d]
        assert p['valid']==(case not in DIFF) and r['status']==('drift' if case in DIFF else 'valid') and r['filesWritten']==len(repeat)*2
    assert [x['phase'] for x in r['trace']]==(['validate-input'] if reject else ['validate-input','render-first','render-repeat','inject-fault','validate-contract'])
    elapsed=[x['elapsedNs'] for x in r['trace']];assert elapsed==sorted(elapsed) and all(type(x) is int and x>=0 for x in elapsed)
    for x in r['trace']:datetime.datetime.fromisoformat(x['utc'])
    return {'validScenario':True,'status':r['status'],'files':sorted(r['tree']),'missing':r.get('report',{}).get('missing',[]),'changed':r.get('report',{}).get('changed',[]),'reason':r['reason']}
