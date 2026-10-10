#!/usr/bin/env python3
import hashlib,json,pathlib,shutil,sys,tempfile
sys.dont_write_bytecode=True
import checker
ROOT=pathlib.Path(__file__).resolve().parent
def fp():return {str(p.relative_to(ROOT)):(hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_mtime_ns) for p in ROOT.rglob('*') if p.is_file()}
def main():
    run=ROOT/(ROOT/'CURRENT').read_text().strip();before=fp();checker.check(run);assert before==fp();out=[{'test':'read-only SHA256 + mtime_ns','passed':True}]
    for kind in ['false-reader-success','false-db-restored','wrong-active','false-health-pass','changed-matrix','changed-migration']:
        with tempfile.TemporaryDirectory(prefix='rollback-negative-') as td:
            temp=pathlib.Path(td)/'run';shutil.copytree(run,temp);d=json.loads((temp/'result.json').read_text());t=d['releases'][1]['trace']
            if kind=='false-reader-success':
                cmd=t[6]['command'];cmd['exitCode']=0;cmd['parsed']={'version':'v1','sql':'SELECT id, name FROM person ORDER BY id','rows':[[1,'Ada']]};cmd['stdout']=json.dumps(cmd['parsed'])+'\n';d['releases'][1]['v1ReadExit']=0;d['releases'][1]['v1ReadSucceeded']=True
            if kind=='false-db-restored':d['releases'][1]['databaseRestored']=True
            if kind=='wrong-active':t[5]['active']=d['releases'][1]['trace'][2]['active']
            if kind=='false-health-pass':
                h=t[4]['command'];h['exitCode']=0;h['parsed']['healthy']=True;h['stdout']=json.dumps(h['parsed'])+'\n'
            if kind=='changed-matrix':d['matrix'][2]['reads']['v1']['exitCode']=0
            if kind=='changed-migration':t[1]['sqlTrace'][0]['sql']='SELECT 1'
            (temp/'result.json').write_text(json.dumps(d));(temp/'stdout.json').write_text(json.dumps(d)+'\n')
            artifacts={str(p.relative_to(temp)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in temp.rglob('*') if p.is_file() and p.name!='artifacts.json'};(temp/'artifacts.json').write_text(json.dumps(artifacts))
            try:checker.check(temp)
            except AssertionError as e:out.append({'test':kind,'passed':True,'rawDerivedHashesConsistent':True,'oracleRejection':str(e)})
            else:raise AssertionError('accepted '+kind)
    assert before==fp();print(json.dumps(out,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
