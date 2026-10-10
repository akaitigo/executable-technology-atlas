import datetime,hashlib,json,pathlib,platform,sys
from calculate import calculate
ROOT=pathlib.Path(__file__).resolve().parent
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def run(case,offset):
    fixture=json.loads((ROOT/'fixtures.json').read_text())[case]
    return dict(case=case,offset=offset,fixture=fixture,utc=utc(),runtime={'python':platform.python_version(),'platform':platform.system()},source_binding={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ['calculate.py','runner.py','fixtures.json','hand-oracle.json']},result=calculate(fixture,offset))
def batch():return {c+'@'+str(o):run(c,o) for c in json.loads((ROOT/'fixtures.json').read_text()) for o in [0,1]}
if __name__=='__main__':
    if sys.argv[1:]!=['--record']:raise SystemExit('explicit --record required; checker and route are read-only')
    folder=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    folder.mkdir(parents=True);(folder/'raw.json').write_text(json.dumps(batch(),indent=2)+'\n');print(folder.relative_to(ROOT))
