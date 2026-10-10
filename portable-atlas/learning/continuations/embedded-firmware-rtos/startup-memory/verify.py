"""Atlas: read saved bytes against the preimplementation hand table; never run the model."""
import argparse,copy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)
def check(result):
    hand=json.loads((ROOT/'hand-oracle.json').read_text());fixture=json.loads((ROOT/'fixtures.json').read_text())
    assert result['status']=='observed' and result['schema']==1 and type(result['schema']) is int
    assert result['priority_observed']==10 and result['fixture_sha256']==sha(ROOT/'fixtures.json')
    assert canonical(result['scope'])==canonical({'model_only':True,'linker_runs':0,'compiler_runs':0,'device_access':0,'cpu_instruction_execution':0,'browser_executed':False,'server_started':False})
    assert canonical(result['cases'])==canonical(hand['cases'])
    reasons=[('size-bool','INTEGER_REQUIRED'),('rom-short','MEMORY_BYTES'),('byte-bool','MEMORY_BYTES'),('byte-over','MEMORY_BYTES'),('rom-changed','FIXED_MEMORY'),('ram-changed','FIXED_MEMORY'),('missing-field','SCHEMA'),('extra-field','SCHEMA'),('negative-source','MAP_RANGE'),('overlap','OVERLAP'),('guard-overlap','GUARD_RANGE'),('bss-over','MAP_RANGE'),('negative-length','MAP_RANGE'),('float-length','INTEGER_REQUIRED'),('unknown-operation','CASE_SCHEMA'),('unapproved-overrun','CASE_SCHEMA'),('unknown-case','UNKNOWN_CASE')]
    expected=[{'id':n,'status':'INPUT_REFUSED','reason':reason,'write_count':0,'main':None} for n,reason in reasons]
    assert canonical(result['input_refusals'])==canonical(expected)
    for r,c in zip(result['cases'],fixture['cases']):
        copy_addresses=set(range(2,2+c['data_length']));zero_addresses=set(range(8,8+c['bss_length']))
        outside=[w['ram_offset'] for w in r['writes'] if w['ram_offset'] not in (copy_addresses if w['phase']=='copy' else zero_addresses)]
        assert outside==([6] if c['id']=='copy-one-past' else [])
        assert r['final_rom']==fixture['rom'] and r['write_count']==len(r['writes'])
    assert sum(len(r['writes']) for r in result['cases'])==41
    assert sum(len(r['snapshots']) for r in result['cases'])==26
    assert sum(r['classification']=='NORMAL' for r in result['cases'])==3
    return {'fixed_cases':7,'writes':41,'snapshots':26,'main_observations':7,'input_refusals':17,'normal':3,'intentional_faults':4}

def mutants(result):
    changes=[
        ('copy-byte',lambda r:r['cases'][0]['final_ram'].__setitem__(2,18)),
        ('zero-byte',lambda r:r['cases'][0]['final_ram'].__setitem__(8,165)),
        ('rom-mutation',lambda r:r['cases'][0]['final_rom'].__setitem__(0,0)),
        ('hidden-write',lambda r:r['cases'][5]['writes'].pop(4)),
        ('guard-hidden',lambda r:r['cases'][5]['final_ram'].__setitem__(6,204)),
        ('early-read-replaced',lambda r:r['cases'][4]['main'].update(data=[17,34,51,68])),
        ('early-final-used-as-success',lambda r:r['cases'][4].update(classification='NORMAL')),
        ('empty-write',lambda r:r['cases'][6].update(write_count=1)),
        ('wrong-source',lambda r:r['cases'][0]['writes'][0].update(rom_offset=2)),
        ('wrong-old-byte',lambda r:r['cases'][0]['writes'][0].update(before=0)),
        ('float-byte',lambda r:r['cases'][0]['final_ram'].__setitem__(2,17.0)),
        ('refusal-main',lambda r:r['input_refusals'][0].update(main={})),
        ('scope-device-claim',lambda r:r['scope'].update(device_access=1)),
    ];found=[]
    for name,change in changes:
        r=copy.deepcopy(result);change(r)
        try:check(r)
        except (AssertionError,KeyError,TypeError,ValueError):found.append(name)
        else:raise AssertionError('mutant not rejected: '+name)
    return found

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run',help='saved directory relative to this lesson');a=parser.parse_args();directory=(ROOT/a.run).resolve()
    assert ROOT/'observations' in directory.parents
    report=json.loads((directory/'report.json').read_text());assert report['status']=='observed' and report['child_reaped'] and report['exit_code']==0
    assert report['result_sha256']==sha(directory/'result.json')
    for name,digest in report['sources'].items():assert sha(ROOT/name)==digest,name
    for name in ['stdout','stderr']:assert report[name+'_sha256']==sha(directory/(name+'.txt'))
    result=json.loads((directory/'result.json').read_text());assert canonical(json.loads((directory/'stdout.txt').read_text()))==canonical(result)
    for name,digest in json.loads((ROOT/'contract-lock.json').read_text())['files'].items():assert sha(ROOT/name)==digest,name
    print(json.dumps({'title':'Atlas saved startup verification','passed':True,**check(result),'mutation_refusals':mutants(result),'model_rerun':False,'source_sha256':sha(Path(__file__)),'run':a.run}))
if __name__=='__main__':main()
