"""Atlas: inspect saved actual WASI results against fixed symbolic rights and errno expectations."""
import argparse,copy,hashlib,json
from pathlib import Path
from decode_module import verify_binary
ROOT=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(value,label):
 if not value:raise ValueError(label)
def check_case(c,expected):
 cid=expected['id'];need(c['case_id']==cid and c['stage']=='observed' and c['error'] is None,'case identity/state')
 rights=c['rights'];before=rights['directory_before'];after=rights['directory_after'];need(int(before['base'])&8192 and int(before['inheriting'])&2,'initial directory rights')
 need(after['base']==before['base'],'directory base must stay unchanged')
 changed=cid in ['directory-before-open','opened-before-directory-change'];need(int(after['inheriting'])==(int(before['inheriting'])&~2 if changed else int(before['inheriting'])),'only inheriting FD_READ removed')
 if expected['file'] is None:need(rights['file_before'] is None and rights['file_after'] is None,'file not opened')
 else:need(rights['file_before']==expected['file']['before'] and rights['file_after']==expected['file']['after'],'file rights relation')
 want={k:expected[k] for k in ['open_errnos','read_status','read_errno','hex','nread_total','classification']};want['guest_name']='/lesson';need(c['outcome']==want,'outcome')
 events=c['events'];need([e['sequence'] for e in events]==list(range(len(events))),'event numbering');at=0;file_fd=None;read_count=0
 def event(op,role,phase,args=None,errno=0,output=None):
  nonlocal at
  e=events[at];at+=1;need((e['op'],e['role'],e['phase'],e['errno'])==(op,role,phase,errno),'event order/target/errno')
  if args is not None:need(e['wrapper_args']==args,'wrapper arguments')
  if output is not None:need(e['output']==output,'valid output')
  return e
 def stat(role,phase,fd,value):event('fd_fdstat_get',role,phase,[fd],output={**value,'output_used':True})
 def reduce_dir():event('fd_fdstat_set_rights','directory','decrease',[3,before['base'],str(int(before['inheriting'])&~2)]);stat('directory','after',3,after)
 def opened(phase,errno):
  e=event('path_open','directory',phase,[3,128,8],errno)
  if errno:need(e['output']=={'opened_fd':None,'output_used':False},'refused open has no valid FD');return None
  fd=e['output']['opened_fd'];need(type(fd)==int and 3<fd<2**32-1 and e['output']['output_used'] is True,'returned FD');return fd
 event('fd_prestat_get','directory','discover',[3],output={'name_length':7,'output_used':True});event('fd_prestat_dir_name','directory','discover',[3,7],output={'guest_name':'/lesson','output_used':True});stat('directory','before',3,before)
 if cid=='directory-before-open':reduce_dir()
 file_fd=opened('first_open',expected['open_errnos'][0])
 if file_fd is not None:
  stat('file','before',file_fd,rights['file_before'])
  if cid=='file-read-reduced':event('fd_fdstat_set_rights','file','decrease',[file_fd,'0','0']);stat('file','after',file_fd,rights['file_after'])
  elif cid=='opened-before-directory-change':reduce_dir();stat('file','after',file_fd,rights['file_after'])
  if cid=='file-read-reduced':event('fd_read','file','read',[file_fd],76,{'nread':None,'hex':None,'output_used':False});read_count=1
  else:
   content=b'';eof=False
   while at<len(events) and events[at]['op']=='fd_read':
    need(not eof,'read after EOF');e=event('fd_read','file','read',[file_fd]);v=e['output'];b=bytes.fromhex(v['hex']);need(type(v['nread'])==int and len(b)==v['nread']<=8 and v['output_used'] is True,'read value');read_count+=1;need(read_count<=8,'bounded reads');content+=b;eof=v['nread']==0
   need(eof and read_count>=2 and content.hex()=='41746c61730a','successful bytes then EOF')
  if cid=='granted':stat('file','after',file_fd,rights['file_after'])
  if cid=='opened-before-directory-change':opened('new_open_after_change',76)
  event('fd_close','file','cleanup',[file_fd])
 event('fd_close','directory','cleanup',[3]);need(at==len(events),'unexpected later event')
 cleanup=c['cleanup'];need(cleanup['complete'] is True and cleanup['preopen_created'] and cleanup['guest_initialized'] and cleanup['preopen_close_errno']==0 and cleanup['remaining_file_fds']==[] and not cleanup['guest_preopen_close_unconfirmed'],'guest cleanup')
 need(cleanup['file_closes']==([{'fd':file_fd,'errno':0}] if file_fd is not None else []),'only allocated file closed')
 return {'case_id':cid,'events':len(events),'read_calls':read_count}
def check(data):
 need(data['status']=='observed' and data['priority_observed']==10 and data['host_fixture_read'] is False and not data['later_cases_not_started'],'execution header')
 need(data['runtime']=={'node':'25.2.1','uvwasi':'0.0.23','wasi':'preview1'},'fixed runtime');need(data['module_sha256']==sha(ROOT/'module.wasm') and data['fixture_sha256']==sha(ROOT/'fixtures.json'),'module/input binding')
 oracle=json.loads((ROOT/'hand-oracle.json').read_text());need(len(data['cases'])==4,'case count');return [check_case(c,e) for c,e in zip(data['cases'],oracle['cases'])]
def verify(run):
 run=run.resolve();need(run.parent==ROOT/'observations','owned saved run');r=json.loads((run/'report.json').read_text());need(r['status']=='observed' and r['child_reaped'] and r['exit_code']==0 and r['output_complete'] and not r['timed_out'] and r['fixture_cleanup'] and not (run/'fixture').exists(),'owned child/fixture terminal')
 need(r['priority_guard']['ready'] and r['priority_guard']['observed_nice']==10,'actual priority');need(sha(ROOT/r['resource_gate_file'])==r['resource_gate_sha256'] and 0<=r['resource_gate_age_seconds']<=60,'fresh resource binding')
 for n,h in r['sources'].items():need(sha(ROOT/n)==h,'execution source '+n)
 for stem in ['stdout','stderr','result']:need(sha(run/r[stem+'_file'])==r[stem+'_sha256'],'saved '+stem)
 lines=[json.loads(line) for line in (run/'stdout.txt').read_text().splitlines()];data=json.loads((run/'result.json').read_text());need(lines[-1]=={'kind':'result','result':data},'stdout/final result');need([x['case'] for x in lines if x['kind']=='case']==data['cases'],'case journal')
 need([{'case_id':x['case_id'],'event':x['event']} for x in lines if x['kind']=='event']==[{'case_id':c['case_id'],'event':e} for c in data['cases'] for e in c['events']],'event journal')
 decoded=verify_binary((ROOT/'module.wasm').read_bytes());cases=check(data);changes=[]
 edits=[('stale_case',lambda d:d['cases'][1].update(case_id='granted')),('directory_base_changed',lambda d:d['cases'][1]['rights']['directory_after'].update(base='0')),('inheriting_not_reduced',lambda d:d['cases'][1]['rights'].update(directory_after=d['cases'][1]['rights']['directory_before'])),('old_fd_rights_revoked',lambda d:d['cases'][3]['rights']['file_after'].update(base='0')),('failed_read_as_EOF',lambda d:next(e for e in d['cases'][2]['events'] if e['op']=='fd_read')['output'].update(nread=0,hex='')),('refused_open_has_old_fd',lambda d:next(e for e in d['cases'][1]['events'] if e['op']=='path_open')['output'].update(opened_fd=4,output_used=True)),('wrong_read_fd',lambda d:next(e for e in d['cases'][0]['events'] if e['op']=='fd_read')['wrapper_args'].__setitem__(0,999)),('wrong_bytes',lambda d:d['cases'][0]['outcome'].update(hex='00')),('missing_cleanup',lambda d:d['cases'][3]['cleanup'].update(complete=False)),('missing_case',lambda d:d['cases'].pop())]
 for name,edit in edits:
  changed=copy.deepcopy(data);edit(changed)
  try:check(changed)
  except (ValueError,KeyError,IndexError,TypeError):changes.append(name)
  else:raise ValueError('undetected change '+name)
 return {'title':'Atlas saved WASI comparison verification','passed':True,'run':str(run.relative_to(ROOT)),'cases':cases,'imports':len(decoded['imports']),'functions':len(decoded['functions']),'alterations_detected':changes,'actual_runtime_started':False,'fixture_read_by_verifier':False}
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True);a=p.parse_args();print(json.dumps(verify(ROOT/a.run),ensure_ascii=False,indent=2))
