"""Atlas: save seven bounded byte-model cases in one existing Python process."""
import copy,datetime,hashlib,json,os,platform
from pathlib import Path
from model import execute
ROOT=Path(__file__).resolve().parent

def refusal_inputs(base):
    changes=[
        ('size-bool','INTEGER_REQUIRED',lambda f:f.update(size=True)),
        ('rom-short','MEMORY_BYTES',lambda f:f['rom'].pop()),
        ('byte-bool','MEMORY_BYTES',lambda f:f['rom'].__setitem__(0,True)),
        ('byte-over','MEMORY_BYTES',lambda f:f['rom'].__setitem__(0,256)),
        ('rom-changed','FIXED_MEMORY',lambda f:f['rom'].__setitem__(4,18)),
        ('ram-changed','FIXED_MEMORY',lambda f:f['ram_initial'].__setitem__(0,0)),
        ('missing-field','SCHEMA',lambda f:f.pop('bss_offset')),
        ('extra-field','SCHEMA',lambda f:f.update(device='real')),
        ('negative-source','MAP_RANGE',lambda f:f.update(data_source_offset=-1)),
        ('overlap','OVERLAP',lambda f:f.update(data_target_offset=8)),
        ('guard-overlap','GUARD_RANGE',lambda f:f.update(guard_offsets=[3,12])),
        ('bss-over','MAP_RANGE',lambda f:f['cases'][0].update(bss_length=12)),
        ('negative-length','MAP_RANGE',lambda f:f['cases'][0].update(data_length=-1)),
        ('float-length','INTEGER_REQUIRED',lambda f:f['cases'][0].update(data_length=4.0)),
        ('unknown-operation','CASE_SCHEMA',lambda f:f['cases'][0].update(operations=['flash'])),
        ('unapproved-overrun','CASE_SCHEMA',lambda f:f['cases'][0].update(copy_one_past=True)),
    ]
    for name,reason,change in changes:
        value=copy.deepcopy(base);change(value);yield name,reason,value,'copy-zero-main'
    yield 'unknown-case','UNKNOWN_CASE',copy.deepcopy(base),'real-boot'

def main():
    priority=os.getpriority(os.PRIO_PROCESS,0)
    if priority!=10:raise RuntimeError('actual nice 10 required before model execution')
    fixture=json.loads((ROOT/'fixtures.json').read_text());results=[execute(fixture,c['id']) for c in fixture['cases']];refusals=[]
    for name,reason,value,case_id in refusal_inputs(fixture):
        try:execute(value,case_id)
        except ValueError as e:
            assert str(e)==reason,(name,str(e),reason)
            refusals.append({'id':name,'status':'INPUT_REFUSED','reason':str(e),'write_count':0,'main':None})
        else:raise AssertionError('invalid input accepted: '+name)
    out={'title':'Atlas startup memory saved calculation','schema':1,'status':'observed','observed_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'runtime':{'python':platform.python_version(),'platform':platform.platform(),'machine':platform.machine()},'priority_observed':priority,
         'fixture_sha256':hashlib.sha256((ROOT/'fixtures.json').read_bytes()).hexdigest(),'cases':results,'input_refusals':refusals,
         'scope':{'model_only':True,'linker_runs':0,'compiler_runs':0,'device_access':0,'cpu_instruction_execution':0,'browser_executed':False,'server_started':False}}
    print(json.dumps(out,ensure_ascii=False,allow_nan=False))
if __name__=='__main__':main()
