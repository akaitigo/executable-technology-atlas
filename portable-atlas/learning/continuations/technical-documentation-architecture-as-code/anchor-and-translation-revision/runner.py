import datetime,hashlib,json,pathlib,platform,sys,tempfile
from calculate import validate
ROOT=pathlib.Path(__file__).resolve().parent
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(case):
    f=json.loads((ROOT/'fixtures.json').read_text())[case];folder=tempfile.TemporaryDirectory(prefix='atlas-anchor-',dir='/private/tmp');root=pathlib.Path(folder.name)
    try:
        assert set(f['pages'])=={'api.html','ja.html','guide.html'}
        for name,text in f['pages'].items():(root/name).write_text(text)
        (root/'manifest.json').write_text(json.dumps(f['manifest'],ensure_ascii=False,sort_keys=True))
        result=validate(root,f['mode'])
    finally:folder.cleanup()
    assert not root.exists()
    return dict(case=case,fixture=f,utc=utc(),runtime={'python':platform.python_version(),'platform':platform.system()},owned_tmp_cleaned=True,source_binding={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['calculate.py','runner.py','fixtures.json','hand-oracle.json']},result=result)
if __name__=='__main__':
    if sys.argv[1:]!=['--record']:raise SystemExit('explicit --record required')
    p=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');p.mkdir(parents=True)
    (p/'raw.json').write_text(json.dumps({c:run(c) for c in json.loads((ROOT/'fixtures.json').read_text())},ensure_ascii=False,indent=2)+'\n');print(p.relative_to(ROOT))
