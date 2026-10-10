#!/usr/bin/env python3
import copy,hashlib,json,pathlib,shutil,tempfile
import sys
sys.dont_write_bytecode=True
import checker
R=pathlib.Path(__file__).resolve().parent
run=R/(R/'CURRENT').read_text().strip()
def fingerprint():return {str(p.relative_to(R)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in R.rglob('*') if p.is_file()}
def mutate(d,kind):
    c=d['cases'][0]; t={e['label']:e for e in c['trace']}
    if kind=='snapshot':t['held']['rows']=[[20]]
    if kind=='checkpoint-complete':t['checkpoint-held']['rows']=[[0,1,1]]
    if kind=='busy-flag':t['checkpoint-held']['rows']=[[1,1,0]]
    if kind=='connection':t['held']['connection']='writer'
    if kind=='sequence':c['trace'][12],c['trace'][13]=c['trace'][13],c['trace'][12]
    if kind=='sql':t['reader-begin']['sql']='BEGIN IMMEDIATE'
    if kind=='fresh':t['fresh']['rows']=[[10]]
def main():
    before=fingerprint(); checker.check(run); assert before==fingerprint(); outcomes=[{'test':'read-only SHA256 + mtime_ns','passed':True}]
    for kind in ['snapshot','checkpoint-complete','busy-flag','connection','sequence','sql','fresh']:
        with tempfile.TemporaryDirectory(prefix='wal-negative-') as td:
            temp=pathlib.Path(td)/'run'; shutil.copytree(run,temp)
            d=json.loads((temp/'result.json').read_text()); mutate(d,kind)
            (temp/'result.json').write_text(json.dumps(d));(temp/'stdout.ndjson').write_text(''.join(json.dumps(c)+'\n' for c in d['cases']))
            artifacts={str(p.relative_to(temp)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in temp.rglob('*') if p.is_file() and p.name!='artifacts.json'}
            (temp/'artifacts.json').write_text(json.dumps(artifacts))
            try:checker.check(temp)
            except AssertionError as e:outcomes.append({'test':kind,'passed':True,'independentOracleRejected':str(e),'rawAndDerivedAndArtifactHashesConsistent':True})
            else:raise AssertionError('accepted '+kind)
    assert before==fingerprint(); print(json.dumps(outcomes,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
