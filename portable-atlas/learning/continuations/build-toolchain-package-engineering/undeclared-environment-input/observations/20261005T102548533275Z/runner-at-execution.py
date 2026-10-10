"""Owned real-clang experiment; no inherited system environment collection."""
import argparse, datetime, hashlib, json, pathlib, platform, shutil, subprocess, tempfile
ROOT=pathlib.Path(__file__).resolve().parent
CLANG=pathlib.Path('/usr/bin/clang')
FLAGS=['-std=c11','-O0','-Wall','-Wextra']
SOURCE=b'#include <banner.h>\nextern int puts(const char *);\nint main(void) { return puts(BANNER) < 0; }\n'
HEADERS={'A':b'#define BANNER "A"\n','B':b'#define BANNER "B"\n'}
def sha(path):
    h=hashlib.sha256()
    with pathlib.Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def key(payload):return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def run(record=False):
    if not CLANG.is_file():raise RuntimeError('existing clang unavailable; no toy substitution')
    observations=ROOT/'observations';work_root=observations/'work';work_root.mkdir(exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination=observations/stamp if record else None
    if destination:destination.mkdir()
    events=[]
    with tempfile.TemporaryDirectory(dir=work_root) as temp:
        work=pathlib.Path(temp)
        (work/'tmp').mkdir();(work/'cache').mkdir();(work/'outputs').mkdir()
        for letter,data in HEADERS.items():
            folder=work/'headers'/letter;folder.mkdir(parents=True);(folder/'banner.h').write_bytes(data)
        (work/'main.c').write_bytes(SOURCE)
        def env(letter):return {'PATH':'/usr/bin:/bin','LC_ALL':'C','TMPDIR':str(work/'tmp'),'CPATH':'headers/'+letter}
        def invoke(argv,environment):
            began=datetime.datetime.now(datetime.timezone.utc).isoformat()
            p=subprocess.run(argv,cwd=work,env=environment,capture_output=True,timeout=20)
            # Only owned temp prefix is normalized; no global env or private host paths gathered.
            clean=lambda data:data.decode(errors='replace').replace(str(work),'$WORK')
            event={'utc':began,'argv':argv,'env':{k:v.replace(str(work),'$WORK') for k,v in environment.items()},'stdout':clean(p.stdout),'stderr':clean(p.stderr),'exit':p.returncode}
            events.append(event)
            if p.returncode:raise RuntimeError(json.dumps(event))
            return event
        version=invoke([str(CLANG),'--version'],env('A'))
        identity={'invoked_path':str(CLANG),'resolved_path':str(CLANG.resolve()),'sha256':sha(CLANG),'version':version['stdout']}
        attempts=[]
        sequence=[('bad-A','bad','A'),('good-A','good','A'),('bad-B','bad','B'),('clean-B','clean','B'),('good-B','good','B')]
        for name,mode,letter in sequence:
            dep=invoke([str(CLANG),*FLAGS,'-MM','-MT','app','main.c'],env(letter))
            # Restricted two-header fixture: compiler, not a guessed CPATH, resolves the path.
            tokens=dep['stdout'].replace('\\\n',' ').split(':',1)[1].split()
            header_names=[t for t in tokens if t.endswith('/banner.h')]
            if header_names!=['headers/'+letter+'/banner.h']:raise RuntimeError('unexpected compiler dependency set')
            header=work/header_names[0]
            payload={'source_sha256':sha(work/'main.c'),'compiler':identity,'flags':FLAGS}
            if mode=='good':payload['resolved_headers']=[{'logical_name':'banner.h','sha256':sha(header)}]
            action_key=key(payload);cached=work/'cache'/action_key;hit=cached.exists() and mode!='clean';out=work/'outputs'/name
            if hit:
                shutil.copy2(cached,out);compile_event=None
            else:
                compile_event=invoke([str(CLANG),*FLAGS,'main.c','-o','outputs/'+name],env(letter))
                if mode!='clean':shutil.copy2(out,cached)
            execution=invoke(['./outputs/'+name],{'PATH':'/usr/bin:/bin','LC_ALL':'C'})
            item={'name':name,'mode':mode,'cpath':'headers/'+letter,'resolved_dependencies':tokens,'header_sha256':sha(header),'key_payload':payload,'key':action_key,'cache_hit':hit,'compile':compile_event,'execution':execution,'binary_sha256':sha(out),'binary_size':out.stat().st_size}
            attempts.append(item)
            if destination:shutil.copy2(out,destination/(name+'.bin'))
        if destination:
            shutil.copy2(work/'main.c',destination/'main.c')
            for letter in HEADERS:shutil.copy2(work/'headers'/letter/'banner.h',destination/('banner-'+letter+'.h'))
        report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine()},'compiler':identity,'inputs':{'source_hex':SOURCE.hex(),'headers_hex':{k:v.hex() for k,v in HEADERS.items()}},'attempts':attempts,'commands':events,'recorded':bool(destination),'cleanup':{'owned_temp_removed':True},'source_binding':{name:sha(ROOT/name) for name in ('runner.py','oracle.json')}}
    assert not work.exists()
    if destination:(destination/'raw.json').write_text(json.dumps(report,indent=2)+'\n')
    return report,destination
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');p.add_argument('--inspect-evidence',action='store_true');args=p.parse_args()
    if args.inspect_evidence:
        reports=sorted((ROOT/'observations').glob('*/raw.json'));print(reports[-1].read_text())
    else:
        report,dest=run(args.record);print(json.dumps({'attempts':[{k:v for k,v in a.items() if k in ('name','cache_hit','binary_sha256')}|{'stdout':a['execution']['stdout']} for a in report['attempts']],'record_directory':dest.name if dest else None},indent=2))
