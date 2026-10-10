import argparse,datetime,hashlib,json,pathlib,platform
from solver import experiment
from reference import reference
ROOT=pathlib.Path(__file__).resolve().parent
BOUND=('solver.py','reference.py','runner.py','fixtures.json','oracle.json')
def run(case):
    fixtures=json.loads((ROOT/'fixtures.json').read_text())
    if case not in fixtures:raise ValueError('unsupported fixed fixture')
    f=fixtures[case];r=experiment(f)
    return dict(case=case,utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runtime=dict(python=platform.python_version(),os=platform.system(),machine=platform.machine()),fixture=f,norm='infinity: max absolute component; matrix maximum absolute row sum',result=r,references=reference(f,r),source_binding={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in BOUND})
def record():
    d=ROOT/'observations'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');d.mkdir();(d/'raw.json').write_text(json.dumps({n:run(n) for n in json.loads((ROOT/'fixtures.json').read_text())},indent=2)+'\n');return d
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--record',action='store_true');p.add_argument('--case',choices=json.loads((ROOT/'fixtures.json').read_text()));p.add_argument('--inspect-evidence',action='store_true');a=p.parse_args()
    if a.record:print(record().relative_to(ROOT))
    elif a.case:print(json.dumps(run(a.case),indent=2))
    elif a.inspect_evidence:print(sorted((ROOT/'observations').glob('*/raw.json'))[-1].read_text())
    else:p.error('choose --case, --inspect-evidence or explicit --record')
