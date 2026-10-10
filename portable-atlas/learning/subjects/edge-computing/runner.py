"""--record alone creates a new task-owned model observation."""
import argparse
import hashlib
import itertools
import json
import os
import platform
import subprocess
import sys
from datetime import datetime,timezone
from pathlib import Path
from model import Model
ROOT=Path(__file__).resolve().parent
D={'op':'disconnect'}; R={'op':'reconnect'}
def edit(node,value,wall): return {'op':'edit','node':node,'value':value,'wall_ms':wall}
def deliver(id,**extra): return {'op':'deliver','id':id,**extra}
UPDATES=[D,edit('A',20,100),edit('A',21,90),edit('B',30,80),R]
CASES={
 'connected':{'prefix':[edit('A',20,100),deliver('A1'),edit('B',21,101),deliver('B1')],'packets':[]},
 'offline-logical':{'prefix':UPDATES,'packets':['A1','A2','B1']},
 'offline-wallclock':{'prefix':UPDATES,'packets':['A1','A2','B1'],'policy':'wallclock'},
 'buffer-one':{'prefix':UPDATES,'packets':['A1','B1'],'limit':1},
 'duplicates':{'prefix':UPDATES,'packets':['A1','A2','B1','A2']},
 'conflicting-duplicate':{'prefix':UPDATES,'packets':['A1','A2','B1'],'suffix':[deliver('A1',tamper_value=99)]},
 'invalid-value':{'prefix':[D,edit('A',True,100),edit('B',101,100),R],'packets':[]},
 'invalid-limit-zero':{'prefix':[D,edit('A',20,100),R],'packets':[],'limit':0},
 'invalid-limit-bool':{'prefix':[D,edit('A',20,100),R],'packets':[],'limit':True},
 'empty':{'prefix':[D,R],'packets':[]},
 'central-offline':{'prefix':UPDATES,'packets':[],'placement':'central'},
 'central-connected':{'prefix':[edit('A',20,100),deliver('A1'),edit('B',21,101),deliver('B1')],'packets':[],'placement':'central'},
 'zero-value':{'prefix':[D,edit('A',0,0),deliver('A1'),R],'packets':['A1']},
}
def now(): return datetime.now(timezone.utc).isoformat()
def sha(raw): return hashlib.sha256(raw).hexdigest()
def write(path,value): path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--record',action='store_true')
    if not parser.parse_args().record: raise SystemExit('No files changed. Use checker.py for read-only checks; --record for explicit observation update.')
    token=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ-edge')
    folder=ROOT/'observations'/token; folder.mkdir(parents=True)
    run={'execution_id':token,'started_at':now(),'environment':{'python':platform.python_version(),'os':platform.system(),'os_release':platform.release(),'machine':platform.machine(),'dependencies':'stdlib only'},'scope':'two-node model; no edge device or network latency measured','source_digests':{name:sha((ROOT/name).read_bytes()) for name in ('model.py','runner.py','checker.py','quick_validate.py','README.md','sources.json','index.html','app.js','styles.css','skills/atlas-edge-computing/SKILL.md')}}
    observations=[]
    for name,spec in CASES.items():
        case=folder/name; case.mkdir()
        config={'policy':spec.get('policy','logical'),'limit':spec.get('limit',4),'placement':spec.get('placement','edge'),'cost_model':{'edge_edit_ms':2,'remote_rtt_ms':80,'remote_compute_ms':5}}
        write(case/'input.json',{'config':config,**spec})
        sequences=[]
        for number,schedule in enumerate(sorted(set(itertools.permutations(spec['packets'])))):
            operations=spec['prefix']+[deliver(x) for x in schedule]+spec.get('suffix',[])
            result=Model(config).execute(operations)
            record={'sequence':number,'delivery_order':schedule,'operations':operations,'result':result}
            write(case/f'sequence-{number:02}.json',record); sequences.append(record)
        observations.append({'id':name,'input':{'config':config,**spec},'sequences':sequences})
    run['completed_at']=now(); write(folder/'run.json',run)
    write(folder/'command.json',{'command':['python3','runner.py','--record'],'started_at':run['started_at'],'completed_at':run['completed_at'],'model_execution':'completed; independent oracle pending','stdout':'','stderr':''})
    oracle_command=subprocess.run([sys.executable,'checker.py','--oracle-json',str(folder)],cwd=ROOT,capture_output=True,text=True,timeout=15,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    write(folder/'oracle-command.json',{'command':['python3','checker.py','--oracle-json',f'observations/{token}'],'exit_code':oracle_command.returncode,'stdout':oracle_command.stdout,'stderr':oracle_command.stderr.replace(str(ROOT),'<module>')})
    if oracle_command.returncode: raise SystemExit('oracle failed; retained run, prior UI unchanged')
    oracle=json.loads(oracle_command.stdout); write(folder/'oracle-report.json',oracle)
    if not all(x['matches'] for x in oracle['rows']): raise SystemExit('oracle mismatch; retained run, prior UI unchanged')
    write(folder/'artifact-index.json',{p.relative_to(folder).as_posix():sha(p.read_bytes()) for p in sorted(folder.rglob('*')) if p.is_file()})
    payload={'directory':f'observations/{token}','run':run,'observations':observations,'oracle':oracle}
    (ROOT/'observation-data.js').write_text('window.EDGE_OBSERVATION = '+json.dumps(payload,ensure_ascii=False)+';\n')
    print(json.dumps({'run':token,'cases':len(observations),'sequences':len(oracle['rows']),'oracle_matches':True}))
if __name__=='__main__': main()
