import json,pathlib,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[2]
if sys.argv[1:]!=['typed-reference']:
    print(json.dumps({'supported':False,'route':'README unimplemented real-LLM/external-tool/authorization boundary'}));sys.exit(2)
p=subprocess.run([sys.executable,'-B',str(root/'check.py')],cwd=root,capture_output=True,text=True)
if p.returncode:print(p.stderr);sys.exit(p.returncode)
raw=json.loads(sorted((root/'observations').glob('*/raw.json'))[-1].read_text())
print(json.dumps({'supported':True,'checker':json.loads(p.stdout),'normal_final':raw['normal']['result']['final'],'proposal_kept_as_data':raw['normal']['result']['results']['r']['proposed_plan'],'bad_comparisons_are_violations':all(raw[c]['result']['violation'] for c in ('bad-coercion','bad-promotion'))}))
