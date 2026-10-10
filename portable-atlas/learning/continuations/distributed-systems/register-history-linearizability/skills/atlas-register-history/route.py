import json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[2]
if sys.argv[1:]!=['register-history']:
    print(json.dumps({'supported':False,'route':'README unimplemented real-DB/pending/multi-object boundary'}));sys.exit(2)
p=subprocess.run([sys.executable,'-B',str(root/'check.py')],cwd=root,capture_output=True,text=True)
if p.returncode:print(p.stderr);sys.exit(p.returncode)
raw=json.loads(sorted((root/'observations').glob('*/raw.json'))[-1].read_text())
print(json.dumps({'supported':True,'checker':json.loads(p.stdout),'overlap_read_one':raw['overlap-read-one']['result'],'scope':'synthetic complete histories only'}))
