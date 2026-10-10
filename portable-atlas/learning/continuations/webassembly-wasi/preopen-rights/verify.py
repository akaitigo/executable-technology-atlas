"""Atlas: validate saved real WASI records and independently decoded bytes; no new execution."""
import argparse,copy,hashlib,json
from pathlib import Path
from decode_module import verify_binary
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(value,label):
    if not value:raise ValueError(label)

def check_observation(x,case_id,oracle):
    expected=next(c for c in oracle['cases'] if c['id']==case_id)
    need(x['case_id']==case_id,'stale/wrong case');need(x['stage']=='observed' and x['error'] is None,'not observed')
    need(x['outcome']=={k:v for k,v in expected.items() if k!='id'},'outcome mismatch')
    need(x['runtime']['node']=='25.2.1' and x['runtime']['uvwasi']=='0.0.23' and x['runtime']['wasi']=='preview1','runtime binding')
    need(x['host_fixture_read'] is False,'host read is not guest evidence');need(x['cleanup']['complete'],'guest cleanup')
    events=x['events'];need([e['sequence'] for e in events]==list(range(len(events))),'event sequence')
    need(events[0]['op']=='fd_prestat_get' and events[0]['args']==[3] and events[0]['errno']==expected['prestat_errno'],'prestat')
    ops=[e['op'] for e in events]
    if case_id=='no-preopen':
        need(ops==['fd_prestat_get'],'unreachable calls');need(x['cleanup']['file_close_errno'] is None and x['cleanup']['preopen_close_errno'] is None and x['cleanup']['preopen_created'] is False,'no-preopen cleanup');return
    need(ops[:3]==['fd_prestat_get','fd_prestat_dir_name','fd_fdstat_get'],'discovery order')
    need(events[1]['errno']==0 and events[1]['output']=={'guest_name':'/lesson'},'preopen guest name')
    before=x['rights_before'];after=x['rights_after'];need(int(before['base'])&8192 and int(before['inheriting'])&2,'initial required rights')
    expected_prefix=['fd_prestat_get','fd_prestat_dir_name','fd_fdstat_get']
    if case_id=='rights-reduced':
        need(int(after['base'])==int(before['base'])&~8192 and after['inheriting']==before['inheriting'],'reduce only PATH_OPEN')
        need(events[3]['args']==[3,str(int(before['base'])&~8192),before['inheriting']] and events[3]['errno']==0,'rights call')
        expected_prefix+=['fd_fdstat_set_rights','fd_fdstat_get']
    else:need(after==before,'unexpected rights mutation')
    need(ops[:len(expected_prefix)]==expected_prefix,'prefix')
    op=events[len(expected_prefix)];need(op['op']=='path_open' and op['errno']==expected['path_open_errno'],'path open errno')
    need(op['args']==([3,160,10] if case_id=='missing-file' else [3,128,8]),'path bounded argument')
    need(x['cleanup']['preopen_close_errno']==0 and ops[-1]=='fd_close_preopen' and events[-1]['args']==[3] and events[-1]['errno']==0,'preopen closed')
    if case_id!='granted':
        need(op['output']=={'opened_fd':None,'output_used':False},'invalid output read');need(ops==expected_prefix+['path_open','fd_close_preopen'],'read after refusal');need(x['cleanup']['file_close_errno'] is None,'no file to close');return
    fd=op['output']['opened_fd'];need(type(fd)==int and 3<fd<2**32-1 and op['output']['output_used'],'returned file FD')
    reads=events[len(expected_prefix)+1:-2];need(2<=len(reads)<=8,'read bound')
    data=b''
    for i,e in enumerate(reads):
        need(e['op']=='fd_read' and e['args']==[fd] and e['errno']==0,'guest file read')
        v=e['output'];b=bytes.fromhex(v['hex']);need(v['output_used'] and len(b)==v['nread']<=8,'read output bound')
        need((len(b)==0)==(i==len(reads)-1),'EOF position');data+=b
    need(data.hex()==expected['hex'] and len(data)==expected['nread_total'],'read bytes')
    need(events[-2]['op']=='fd_close_file' and events[-2]['args']==[fd] and events[-2]['errno']==0 and x['cleanup']['file_close_errno']==0,'file closed')

def verify(run):
    need(run.is_dir() and run.parent==ROOT/'observations','owned saved run')
    j=json.loads((run/'report.json').read_text());need(j['status']=='observed' and j['fixture_cleanup'] and j['all_children_reaped'],'batch terminal')
    need(not (run/'fixture').exists(),'fixture remains');need(not j['later_cases_not_started'],'missing cases')
    source_root=ROOT
    if run.name=='runtime-20261006T134814277752Z':
        source_root=ROOT/'observations/executed-source'
        manifest=json.loads((source_root/'manifest.json').read_text())
        need(manifest['report_sha256']==sha(run/'report.json') and manifest['files']==j['sources'],'execution snapshot binding')
    for n,h in j['sources'].items():need(sha(source_root/n)==h,'executed source changed: '+n)
    # Only runner and this verifier changed after the recorded run; the guest bytes and observer must still match.
    for n,h in j['sources'].items():
        if n not in ['run.py','verify.py']:need(sha(ROOT/n)==h,'current guest/contract changed: '+n)
    decoded=verify_binary((ROOT/'module.wasm').read_bytes());oracle=json.loads((ROOT/'hand-oracle.json').read_text());need([x['case_id'] for x in j['cases']]==[x['id'] for x in oracle['cases']],'case set')
    observations=[]
    for c in j['cases']:
        need(c['exit_code']==0 and not c['timed_out'] and c['child_reaped'] and c['output_complete'],'child terminal')
        for stem in ['stdout','stderr','observation']:need(sha(run/c[stem+'_file'])==c[stem+'_sha256'],'raw file binding')
        x=json.loads((run/c['stdout_file']).read_text());need(x==json.loads((run/c['observation_file']).read_text()),'stdout/pretty mismatch');need(x['module_sha256']==sha(ROOT/'module.wasm'),'module binding')
        check_observation(x,c['case_id'],oracle);observations.append(x)
    changes=[]
    for label,which,mutation in [
        ('missing outcome',0,lambda x:x.pop('outcome')),
        ('BADF mislabeled as rights',0,lambda x:x['outcome'].update(classification='rights_refusal')),
        ('wrong successful bytes',1,lambda x:x['outcome'].update(hex='00')),
        ('old successful case reused',2,lambda x:x.update(case_id='granted',outcome=copy.deepcopy(observations[1]['outcome']))),
        ('inheriting silently removed',2,lambda x:x['rights_after'].update(inheriting='0')),
        ('missing read appears successful',3,lambda x:x['outcome'].update(read_status='success_then_eof',hex='',nread_total=0)),
        ('cleanup absent',1,lambda x:x['cleanup'].update(complete=False)),
        ('read uses wrong FD',1,lambda x:next(e for e in x['events'] if e['op']=='fd_read')['args'].__setitem__(0,999))]:
        x=copy.deepcopy(observations[which]);mutation(x)
        try:check_observation(x,oracle['cases'][which]['id'],oracle)
        except (ValueError,KeyError):changes.append(label)
        else:raise ValueError('alteration not detected: '+label)
    binary=(ROOT/'module.wasm').read_bytes();bad=[b'bad!'+binary[4:],binary[:-1],binary.replace(b'wasi_snapshot_preview1',b'xasi_snapshot_preview1',1),binary.replace(b'note.txt',b'nope.txt',1)]
    for b in bad:
        try:verify_binary(b)
        except (ValueError,KeyError,IndexError):pass
        else:raise ValueError('binary mutation not detected')
    return {'title':'Atlas 保存WASI結果の検査','passed':True,'run':str(run.relative_to(ROOT)),'executed_source_root':str(source_root.relative_to(ROOT)), 'current_runner_not_reexecuted':source_root!=ROOT,'cases':len(observations),'decoded_functions':len(decoded['functions']),'decoded_imports':len(decoded['imports']),'alterations_detected':changes,'binary_mutations_detected':len(bad),'runtime_executed':False,'observations':observations}

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--run',required=True);a=parser.parse_args();print(json.dumps(verify((ROOT/a.run).resolve()),ensure_ascii=False,indent=2))
