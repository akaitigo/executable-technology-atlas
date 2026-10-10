import argparse,datetime,hashlib,json,pathlib,platform
from executor import execute
ROOT=pathlib.Path(__file__).resolve().parent
def run(case):
    fixtures=json.loads((ROOT/'fixtures.json').read_text())
    if case not in fixtures:raise ValueError('unsupported fixed case')
    return {'case':case,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine()},'input':fixtures[case],'result':execute(fixtures[case]),'source_binding':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('executor.py','runner.py','fixtures.json','oracle.json')}}
def record():
    directory=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');directory.mkdir()
    raw={case:run(case) for case in json.loads((ROOT/'fixtures.json').read_text())}
    (directory/'raw.json').write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n');return directory
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');p.add_argument('--case',choices=json.loads((ROOT/'fixtures.json').read_text()));p.add_argument('--inspect-evidence',action='store_true');args=p.parse_args()
    if args.record:print(record().relative_to(ROOT))
    elif args.inspect_evidence:print(sorted((ROOT/'observations').glob('*/raw.json'))[-1].read_text())
    elif args.case:print(json.dumps(run(args.case),ensure_ascii=False,indent=2))
    else:p.error('choose --case, --inspect-evidence or explicit --record')
