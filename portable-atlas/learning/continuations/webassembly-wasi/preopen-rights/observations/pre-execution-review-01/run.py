"""Atlas: record four bounded, sequential real WASI child processes. Explicit --record only."""
import argparse,datetime,hashlib,json,os,shutil,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
NODE=Path('/opt/homebrew/Cellar/node/25.2.1/bin/node')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--record',action='store_true');args=parser.parse_args()
    if not args.record:parser.error('Atlas: new execution requires --record; use verify.py for saved records')
    fixture=json.loads((ROOT/'fixtures.json').read_text())
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=ROOT/'observations'/('runtime-'+stamp);out.mkdir()
    report={'title':'Atlas 逐次WASI実行ログ','started_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'attempt':1,'retry':0,'node_sha256':sha(NODE),'sources':{n:sha(ROOT/n) for n in ['module.wasm','build-module.cjs','decode_module.py','observe-case.cjs','run.py','verify.py','fixtures.json','hand-oracle.json','module-contract.json']},'cases':[],'status':'preparing','runtime':'Node25.2.1/uvwasi0.0.23/preview1','fixture_cleanup':False,'all_children_reaped':True}
    started=time.monotonic();fixture_dir=out/'fixture'
    try:
        fixture_dir.mkdir();(fixture_dir/'note.txt').write_bytes(bytes.fromhex(fixture['fixture_hex']))
        for case in fixture['cases']:
            if time.monotonic()-started>17:raise RuntimeError('batch deadline: do not start next case')
            name=case['id'];cmd=['/usr/bin/nice','-n','10',str(NODE),str(ROOT/'observe-case.cjs'),name,str(fixture_dir)]
            record={'case_id':name,'command':cmd,'timeout_seconds':3,'stdout_file':name+'.stdout.txt','stderr_file':name+'.stderr.txt','child_started':False,'child_reaped':False}
            # Timeout kills only this directly owned child and communicate() reaps it.
            report['cases'].append(record)
            stdout=stderr=b'';proc=None
            try:
                proc=subprocess.Popen(cmd,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={'PATH':'/usr/bin:/bin:/opt/homebrew/bin','LANG':'C','TZ':'UTC'})
                record.update(child_started=True,owned_child_pid=proc.pid)
                try:stdout,stderr=proc.communicate(timeout=3);record['timed_out']=False
                except subprocess.TimeoutExpired:
                    record['timed_out']=True;proc.kill()
                    try:stdout,stderr=proc.communicate(timeout=2)
                    except subprocess.TimeoutExpired as e:
                        stdout=e.output or b'';stderr=e.stderr or b'';record['output_complete']=False;raise RuntimeError('killed child did not reap within cleanup bound')
                record['output_complete']=True
            finally:
                (out/record['stdout_file']).write_bytes(stdout);(out/record['stderr_file']).write_bytes(stderr)
                record.update(exit_code=proc.returncode if proc else None,child_reaped=proc is not None and proc.poll() is not None,stdout_sha256=sha(out/record['stdout_file']),stderr_sha256=sha(out/record['stderr_file']))
            if proc.returncode!=0 or record['timed_out']:raise RuntimeError('owned child failed; later cases not started')
            data=json.loads(stdout);(out/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');record['observation_file']=name+'.json';record['observation_sha256']=sha(out/record['observation_file'])
            if not data['cleanup']['complete']:raise RuntimeError('guest resources not closed; later cases not started')
        report['status']='observed'
    except Exception as e:report['status']='failed';report['error']={'name':type(e).__name__,'message':str(e)}
    finally:
        try:
            if fixture_dir.exists():shutil.rmtree(fixture_dir)
            report['fixture_cleanup']=not fixture_dir.exists()
        except Exception as e:report['cleanup_error']=str(e);report['status']='failed'
        report['all_children_reaped']=all(c.get('child_reaped',False) for c in report['cases'])
        report['elapsed_seconds']=round(time.monotonic()-started,6);report['finished_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();report['later_cases_not_started']=[c['id'] for c in fixture['cases'] if c['id'] not in [r['case_id'] for r in report['cases']]]
        (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'run':str(out.relative_to(ROOT)),'status':report['status'],'cases':len(report['cases']),'fixture_cleanup':report['fixture_cleanup'],'all_children_reaped':report['all_children_reaped'],'elapsed_seconds':report['elapsed_seconds']},ensure_ascii=False))
    return 0 if report['status']=='observed' and report['fixture_cleanup'] and report['all_children_reaped'] else 1

if __name__=='__main__':raise SystemExit(main())
