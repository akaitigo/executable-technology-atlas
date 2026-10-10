"""--record is the only observation update path; stdlib synthetic calculations."""
import argparse
import copy
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
from calculator import calculate
ROOT=Path(__file__).resolve().parent

def usage(id,sku,qty,team=None):
    row={'id':id,'sku':sku,'quantity':qty}
    if team is not None: row['team']=team
    return row

def base(pool='0.10',weights=None,rows=None,policy='conserved',rates=None):
    return {'scope':'synthetic fixed ratecard and usage; not real market prices, tax or financial advice','currency':'XCU (fictional)','policy':policy,'shared_amount':pool,'weights':{'A':1,'B':1,'C':1} if weights is None else weights,'usage':[] if rows is None else rows,'ratecard':{'small':'0.20','medium':'0.30','large':'0.40'} if rates is None else rates}
EQUAL=[usage('u1','small','1','A'),usage('u2','medium','1','B'),usage('u3','large','1','C')]
CASES={
 'normal-weighted':base('0.12',{'A':1,'B':2},[usage('u1','small','1','A'),usage('u2','small','1','B')]),
 'equal-conserved':base(rows=EQUAL),
 'equal-naive':base(rows=EQUAL,policy='naive'),
 'round-up-conserved':base('0.11'),
 'round-up-naive':base('0.11',policy='naive'),
 'tie-reordered':base(weights={'C':1,'B':1,'A':1},rows=list(reversed(EQUAL))),
 'missing-tag':base(weights={'A':1,'B':1},rows=[usage('u1','small','1','A'),usage('u2','medium','1')]),
 'no-basis':base(weights={},rows=[usage('u1','small','1','A')]),
 'one-cent':base('0.01'),
 'fractional-usage':base(weights={'A':3,'B':1},rates={'frac':'0.105','half':'0.21'},rows=[usage('u1','frac','3','A'),usage('u2','half','0.5','B')]),
 'zero-shared':base('0.00',{'A':1,'B':1},[usage('u1','small','1','A'),usage('u2','small','1','B')]),
 'zero-quantity':base(rows=[usage('u1','small','0','A')]),
 'negative-quantity':base(rows=[usage('u1','small','-1','A')]),
 'float-quantity':base(rows=[usage('u1','small',0.1,'A')]),
 'nonfinite-rate':base(rates={'bad':'NaN'},rows=[usage('u1','bad','1','A')]),
 'duplicate-usage':base(rows=[usage('same','small','1','A'),usage('same','small','1','B')]),
 'zero-weight':base(weights={'A':0}),
}

def now(): return datetime.now(timezone.utc).isoformat()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def write(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--record',action='store_true')
    if not parser.parse_args().record: raise SystemExit('No files changed. checker.py is read-only; --record explicitly creates a new observation.')
    token=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-finops');folder=ROOT/'observations'/token;folder.mkdir(parents=True)
    run={'execution_id':token,'started_at':now(),'environment':{'python':platform.python_version(),'os':platform.system(),'os_release':platform.release(),'machine':platform.machine(),'dependencies':'stdlib only'},'scope':'synthetic ratecard/usage/allocation model; no pricing/billing/tax API or financial advice','source_digests':{name:sha((ROOT/name).read_bytes()) for name in ('calculator.py','runner.py','checker.py','quick_validate.py','README.md','sources.json','index.html','app.js','styles.css','skills/atlas-finops-cost-engineering/SKILL.md')}}
    cases=[]
    for id,data in CASES.items():
        case=folder/id;case.mkdir();write(case/'input.json',data)
        result=calculate(copy.deepcopy(data));write(case/'result.json',result)
        cases.append({'id':id,'input':data,'result':result})
    run['completed_at']=now();write(folder/'run.json',run)
    write(folder/'command.json',{'command':['python3','runner.py','--record'],'started_at':run['started_at'],'completed_at':run['completed_at'],'calculation':'completed; oracle pending','stdout':'','stderr':''})
    command=subprocess.run([sys.executable,'checker.py','--oracle-json',str(folder)],capture_output=True,text=True,cwd=ROOT,timeout=15,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    write(folder/'oracle-command.json',{'command':['python3','checker.py','--oracle-json',f'observations/{token}'],'exit_code':command.returncode,'stdout':command.stdout,'stderr':command.stderr.replace(str(ROOT),'<module>')})
    if command.returncode: raise SystemExit('oracle command failed; previous pointer unchanged')
    oracle=json.loads(command.stdout);write(folder/'oracle-report.json',oracle)
    if not all(x['matches'] for x in oracle['rows']): raise SystemExit('oracle mismatch; retained raw run, previous pointer unchanged')
    write(folder/'artifact-index.json',{p.relative_to(folder).as_posix():sha(p.read_bytes()) for p in sorted(folder.rglob('*')) if p.is_file()})
    (ROOT/'observation-data.js').write_text('window.FINOPS_OBSERVATION = '+json.dumps({'directory':f'observations/{token}','run':run,'cases':cases,'oracle':oracle},ensure_ascii=False)+';\n')
    print(json.dumps({'run':token,'cases':len(cases),'independent_oracle_matches':True}))
if __name__=='__main__':main()
