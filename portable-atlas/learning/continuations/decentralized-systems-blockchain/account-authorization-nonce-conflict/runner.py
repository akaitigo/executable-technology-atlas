import datetime,hashlib,json,pathlib,platform,sys
from calculate import calculate
ROOT=pathlib.Path(__file__).resolve().parent
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(case):
    f=json.loads((ROOT/'fixtures.json').read_text())[case]
    return dict(case=case,fixture=f,utc=utc(),runtime={'python':platform.python_version(),'platform':platform.system()},source_binding={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['calculate.py','runner.py','fixtures.json','hand-oracle.json']},result=calculate(f))
if __name__=='__main__':
    if sys.argv[1:]!=['--record']:raise SystemExit('explicit --record required')
    p=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');p.mkdir(parents=True);(p/'raw.json').write_text(json.dumps({c:run(c) for c in json.loads((ROOT/'fixtures.json').read_text())},indent=2)+'\n');print(p.relative_to(ROOT))
