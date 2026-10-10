import argparse,datetime,hashlib,json,pathlib,platform
from language import execute
ROOT=pathlib.Path(__file__).resolve().parent
def run(case):
    fixtures=json.loads((ROOT/'fixtures.json').read_text())
    if case not in fixtures:raise ValueError('unsupported fixed AST')
    input_value=fixtures[case]
    return {'case':case,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runtime':{'python':platform.python_version(),'os':platform.system(),'release':platform.release(),'machine':platform.machine()},'input':input_value,'result':execute(input_value['ast'],input_value['mode']),'source_binding':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in ('language.py','runner.py','fixtures.json','oracle.json')}}
def record():
    path=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');path.mkdir();value={case:run(case) for case in json.loads((ROOT/'fixtures.json').read_text())};(path/'raw.json').write_text(json.dumps(value,indent=2)+'\n');return path
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');p.add_argument('--case',choices=json.loads((ROOT/'fixtures.json').read_text()));p.add_argument('--inspect-evidence',action='store_true');args=p.parse_args()
    if args.record:print(record().relative_to(ROOT))
    elif args.case:print(json.dumps(run(args.case),indent=2))
    elif args.inspect_evidence:print(sorted((ROOT/'observations').glob('*/raw.json'))[-1].read_text())
    else:p.error('choose --case, --inspect-evidence or explicit --record')
