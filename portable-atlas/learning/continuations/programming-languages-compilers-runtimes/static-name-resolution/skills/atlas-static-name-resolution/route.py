import json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[2]
if sys.argv[1:]!=['name-resolution']:
    print(json.dumps({'supported':False,'route':'README unsupported JS-TDZ/closures/typechecking/arbitrary-source'}));sys.exit(2)
p=subprocess.run([sys.executable,'-B',str(root/'check.py')],cwd=root,capture_output=True,text=True)
if p.returncode:print(p.stderr);sys.exit(p.returncode)
raw=json.loads(sorted((root/'observations').glob('*/raw.json'))[-1].read_text())
print(json.dumps({'supported':True,'checker':json.loads(p.stdout),'before_inner_let':{k:raw['before-inner-let']['result'][k] for k in ('bindings','values','evaluation_started')},'scope':'finite authored sequential-declaration AST'}))
