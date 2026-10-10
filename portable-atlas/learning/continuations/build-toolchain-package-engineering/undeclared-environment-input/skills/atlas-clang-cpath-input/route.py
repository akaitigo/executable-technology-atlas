import json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[2]
if sys.argv[1:]!=['cpath-cache']:
    print(json.dumps({'supported':False,'route':'README unimplemented SDK/linker/cross-OS/signing boundary'}));sys.exit(2)
p=subprocess.run([sys.executable,'-B',str(root/'check.py')],cwd=root,capture_output=True,text=True)
if p.returncode:print(p.stderr);sys.exit(p.returncode)
raw=json.loads(sorted((root/'observations').glob('*/raw.json'))[-1].read_text())
print(json.dumps({'supported':True,'checker':json.loads(p.stdout),'observed':{a['name']:a['execution']['stdout'] for a in raw['attempts']},'judgment':'bad-B hit returns stale A; clean-B/good-B return B; no whole hermeticity guarantee'}))
