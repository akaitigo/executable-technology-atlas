"""Default checks saved evidence read-only. --record explicitly executes cycles."""
import argparse,copy,datetime,hashlib,json,re,tempfile
from pathlib import Path
import runner,oracle
ROOT=runner.ROOT
FILES=['fixture.json','runner.py','oracle.py','checker.py','server.py','index.html','app.js','README.md','sources.json','skills/atlas-resilience-continuity-disaster-recovery/SKILL.md']
def hashes():return {n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in FILES}
def docs(record=False):
    for n in ('README.md','index.html'):
        text=(ROOT/n).read_text();links=re.findall(r'\]\(([^)]+)\)',text) if n.endswith('.md') else re.findall(r'(?:href|src)="([^"]+)"',text)
        for link in links:
            if link.startswith(('http:','https:','data:','#')):continue
            if record and link in ('observations/run.json','observations/qa.json') and not (ROOT/link).exists():continue
            assert (ROOT/link).is_file(),(n,link)
        assert all(x in text for x in ('予想','原典','限界','未実施','Resilience','durability','DR strategy','Business continuity'))
    sources=json.loads((ROOT/'sources.json').read_text());assert len(sources)==9 and all(x['locator'] and x['binding'] and x['url'].startswith('https://') for x in sources)
def mutants(raw):
    detected=[]
    for kind in ('stale-as-fresh','gap-zero','missing-count-zero','accepted-corrupt','refusal-live-replaced','false-hash','wrong-duration','wrong-phase','wrong-snapshot'):
        r=copy.deepcopy(raw[2 if kind in ('accepted-corrupt','refusal-live-replaced') else 1])
        if kind=='stale-as-fresh':r['reopenedRows']=oracle.HAND
        elif kind=='gap-zero':r['rpoGapSyntheticTicks']=0
        elif kind=='missing-count-zero':r['dataLossWrites']=0
        elif kind=='accepted-corrupt':r['status']='restored'
        elif kind=='refusal-live-replaced':r['liveAfterHash']='0'*64
        elif kind=='false-hash':r['candidateHash']='0'*64
        elif kind=='wrong-duration':r['attemptObservedNs']+=1
        elif kind=='wrong-phase':r['trace'][0]['phase']='replace-live'
        elif kind=='wrong-snapshot':r['snapshotRows']=[]
        try:oracle.audit(r);raise RuntimeError('survived '+kind)
        except AssertionError:detected.append(kind)
    return detected
def main():
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');a=p.parse_args();docs(a.record);dest=ROOT/'observations/run.json'
    if a.record:
        raw=[]
        for case in runner.fixture()['cases']:
            with tempfile.TemporaryDirectory(prefix='atlas-dr-record-') as folder:
                r=runner.cycle(case,folder);oracle.audit(r,Path(folder));target=ROOT/'observations/artifacts'/case;target.mkdir(parents=True,exist_ok=True)
                for name in r['artifacts']:
                    out=target/name;tmp=out.with_suffix('.tmp');tmp.write_bytes((Path(folder)/name).read_bytes());tmp.replace(out)
                raw.append(r)
        data={'schema':1,'command':'python3 -B checker.py --record','executedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'sourceArtifactDigests':hashes(),'fixtureDigest':runner.digest(runner.fixture()),'raw':raw,'rawDigest':runner.digest(raw),'mutantsDetected':mutants(raw)}
        temp=dest.with_suffix('.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');temp.replace(dest)
    saved=json.loads(dest.read_text());raw=saved['raw'];assert saved['sourceArtifactDigests']==hashes() and saved['fixtureDigest']==runner.digest(runner.fixture()) and saved['rawDigest']==runner.digest(raw)
    assert [r['case'] for r in raw]==list(runner.fixture()['cases'])
    for r in raw:
        cfg=runner.fixture()['cases'][r['case']];assert r['input']==cfg and r['inputDigest']==runner.digest({'config':cfg,'rows':runner.fixture()['rows']});oracle.audit(r,ROOT/'observations/artifacts'/r['case']);assert all(r['environment'].values());assert r['artifacts']['damaged.sqlite']==r['liveBeforeHash'] and r['artifacts'].get('candidate.sqlite')==r['candidateHash']
    assert mutants(raw)==saved['mutantsDetected']
    if not a.record:
        q=json.loads((ROOT/'observations/qa.json').read_text());assert q['sourceArtifactDigests']==hashes() and q['qaDigest']==runner.digest({k:v for k,v in q.items() if k!='qaDigest'})
        assert [x['case'] for x in q['cases']]==list(runner.fixture()['cases'])
        for observed,r in zip(q['cases'],raw):
            assert observed['oracle']==oracle.audit(r)
            o=observed['observed'];assert observed['observedDigest']==runner.digest(o)
            for k in ('inputDigest','status','reason','snapshotRows','latestRows','reopenedRows','missingWriteIds','dataLossWrites','rpoGapSyntheticTicks'):assert o[k]==r[k]
            assert o['candidateMatches']==(r['candidateHash']==r['expectedSnapshotHash']) and o['livePreserved']==(r['liveBeforeHash']==r['liveAfterHash'])
            assert o['attemptObservedNs']==o['restoreAttemptEndNs']-o['restoreAttemptStartNs']>0
            assert o['restoreObservedNs']==(o['attemptObservedNs'] if o['status']=='restored' else None)
            assert o['environment']==r['environment']
            datetime.datetime.fromisoformat(o['executedAtUTC'])
        assert q['rawExpanded'] and q['answerExpanded'] and len(q['roadmapTopics'])==4 and q['cleanup']['serverClosed'] and q['cleanup']['tabClosed']
    print(json.dumps({'status':'PASS','actualCycles':len(raw),'mutantsDetected':len(saved['mutantsDetected']),'artifactFiles':sum(len(r['artifacts']) for r in raw),'sourceArtifacts':len(hashes()),'readOnly':not a.record}))
if __name__=='__main__':main()
