import datetime,hashlib,json,pathlib,platform,sys
import search
ROOT=pathlib.Path(__file__).resolve().parent
SOURCES=['search.py','runner.py','fixtures.json','hand-oracle.json']
def run(case):
    f=json.loads((ROOT/'fixtures.json').read_text())[case]
    return dict(case=case,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runtime=dict(python=platform.python_version(),os=platform.system(),machine=platform.machine()),fixture=f,source_binding={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in SOURCES},result=search.run(f))
if __name__=='__main__':
    if sys.argv[1:]==['--record']:
        directory=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');directory.mkdir()
        (directory/'raw.json').write_text(json.dumps({n:run(n) for n in json.loads((ROOT/'fixtures.json').read_text())},indent=2)+'\n');print(directory.relative_to(ROOT))
    elif len(sys.argv)==3 and sys.argv[1]=='--case':print(json.dumps(run(sys.argv[2]),indent=2))
    else:raise SystemExit('Use --case FIXED_CASE or explicit --record')
