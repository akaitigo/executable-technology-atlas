import datetime,hashlib,json,pathlib,platform,sqlite3,sys,tempfile
import calculate,readback
ROOT=pathlib.Path(__file__).resolve().parent
def run(case,payload=None):
    f=json.loads((ROOT/'fixtures.json').read_text())[case]
    if payload is not None:f['payload']=payload
    with tempfile.TemporaryDirectory(prefix='atlas-outbox-',dir='/private/tmp') as tmp:
        path=pathlib.Path(tmp)/'outbox.sqlite'
        result=calculate.process(path,f);actual=readback.read(path)
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
    assert not pathlib.Path(tmp).exists()
    return dict(case=case,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=platform.python_version(),platform=platform.platform(),sqlite=sqlite3.sqlite_version,fixture=f,result=result,sql_readback=actual,db_sha256_before_cleanup=digest,owned_tmp_cleaned=True,source_binding={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['calculate.py','runner.py','readback.py','fixtures.json','hand-oracle.json','oracle.py']})
if __name__=='__main__':
    if sys.argv[1:]!=['--record']:raise SystemExit('use --record only for new evidence')
    d=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');d.mkdir(parents=True)
    (d/'raw.json').write_text(json.dumps({c:run(c) for c in json.loads((ROOT/'fixtures.json').read_text())},ensure_ascii=False,indent=2)+'\n')
    print(str((d/'raw.json').relative_to(ROOT)))
