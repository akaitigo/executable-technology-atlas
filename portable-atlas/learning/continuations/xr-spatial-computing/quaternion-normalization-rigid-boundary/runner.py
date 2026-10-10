import datetime,hashlib,json,pathlib,platform,sys
from calculate import calculate
ROOT=pathlib.Path(__file__).resolve().parent
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(case,point_x):
    f=json.loads((ROOT/'fixtures.json').read_text())[case]
    return dict(case=case,point_x=point_x,fixture=f,utc=utc(),runtime={'python':platform.python_version(),'platform':platform.system()},source_binding={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['calculate.py','runner.py','fixtures.json','hand-oracle.json']},result=calculate(f,point_x))
if __name__=='__main__':
    if sys.argv[1:]!=['--record']:raise SystemExit('explicit --record required')
    folder=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');folder.mkdir(parents=True)
    raw={c+'@'+str(x):run(c,x) for c in json.loads((ROOT/'fixtures.json').read_text()) for x in (1,2)}
    (folder/'raw.json').write_text(json.dumps(raw,indent=2)+'\n');print(folder.relative_to(ROOT))
