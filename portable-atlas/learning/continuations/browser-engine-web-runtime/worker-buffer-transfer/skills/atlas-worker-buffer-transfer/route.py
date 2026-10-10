import json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[2]
if sys.argv[1:]!=['worker-buffer']:
    print(json.dumps({'supported':False,'route':'README unimplemented speed/process/SAB/Atomics/SW/security boundary'}));sys.exit(2)
p=subprocess.run([sys.executable,'-B',str(root/'check.py')],cwd=root,capture_output=True,text=True)
if p.returncode:print(p.stderr);sys.exit(p.returncode)
print(json.dumps({'supported':True,'checker':json.loads(p.stdout),'scope':'fixed actual Dedicated Worker buffer ownership and serialization'}))
