import datetime,hashlib,json,pathlib,platform,sys
import calculate
ROOT=pathlib.Path(__file__).resolve().parent
def run(case):
    f=json.loads((ROOT/'fixtures.json').read_text())[case]
    return dict(case=case,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=platform.python_version(),platform=platform.platform(),fixture=f,result=calculate.analyze(f),source_binding={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['calculate.py','runner.py','fixtures.json','hand-oracle.json']})
if __name__=='__main__':
    if sys.argv[1:]!=['--record']:raise SystemExit('use --record only for new evidence')
    d=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');d.mkdir(parents=True)
    raw={c:run(c) for c in json.loads((ROOT/'fixtures.json').read_text())}
    (d/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n')
    print(str((d/'raw.json').relative_to(ROOT)))
