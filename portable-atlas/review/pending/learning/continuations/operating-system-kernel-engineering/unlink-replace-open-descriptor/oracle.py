"""No producer, tempfile, or OS observation helper imports."""
import json,sys
from pathlib import Path
P=Path(__file__).resolve().parent;HAND=json.loads((P/'hand-trace.json').read_text())
def check(r,x,literal=None):
 status='EXECUTION_FAILED' if literal and literal.get('status')=='EXECUTION_FAILED' else ('OBSERVED' if x['mode']=='compare' else 'OS_EXCEPTION_OBSERVED')
 assert r['status']==status and r['input_echo']==x and r['mutation_started'] is True
 assert r['durability']=='UNOBSERVED';assert r['cleanup']==dict(all_fds_closed=True,tempdirs_removed=True)
 assert r['environment']['system']=='Darwin';assert r['environment']['python']
 labels=['producer-failure'] if status=='EXECUTION_FAILED' else (['unlink','replace','gap'] if x['mode']=='compare' else [x['mode']])
 assert [run['label'] for run in r['runs']]==labels
 for run in r['runs']:
  label=run['label'];assert run['kind']==('CONTROL_GAP' if label=='gap' else ('OS_EXCEPTION' if x['mode']!='compare' else ('PRODUCER_FAILURE' if label=='producer-failure' else 'NORMAL')))
  ids=run['identities'];assert set(ids)=={'old','new'} and ids['old']!=ids['new'];assert all(len(v)==2 and all(type(n)==int and n>=0 for n in v) for v in ids.values())
  assert run['cleanup']==dict(fd_closed={'old':True,'new':True},fd_fstat_errno={'old':9,'new':9},tempdir_removed=True)
  assert len(run['trace'])==len(HAND[label]);payload={'old':x['old_payload'],'new':x['new_payload']}
  for row,hand in zip(run['trace'],HAND[label]):
   phase,old,olinks,path,plinks,new,nlinks,prepared,error=hand
   assert row['phase']==phase
   for field,role,links in [('old_fd',old,olinks),('new_fd',new,nlinks)]:
    got=row[field]
    if role is None:assert got==dict(state='CLOSED');continue
    assert got['state']=='OPEN' and got['bytes']==payload[role] and got['size']==len(payload[role]) and got['nlink']==links and got['identity']==ids[role]
    assert got['seek_result']==0 and got['offset_after']==len(payload[role]) and got['eof']=='' and got['read_calls']>=1
   got=row['pathname']
   if path is None:assert got==dict(status='ENOENT',bytes=None,identity=None,stat_identity=None,nlink=None,closed_after_probe=None,stat_errno=2,open_errno=2)
   else:
    assert got==dict(status='OPENED',bytes=payload[path],identity=ids[path],stat_identity=ids[path],nlink=plinks,closed_after_probe=True,stat_errno=None,open_errno=None)
   assert row['prepared_path']==dict(status='PRESENT' if prepared else 'ENOENT',identity=ids[prepared] if prepared else None,errno=None if prepared else 2)
  assert run['fsync_calls']==[dict(target=target,status='RETURNED' if x['fsync'] else 'SKIPPED') for target in ['old_fd','new_fd']]
  assert run['gap_callback_count']==(1 if label=='gap' else 0)
  if label in ['missing-source','closed-fd']:assert run['exception']==dict(operation='replace' if label=='missing-source' else 'read',errno=2 if label=='missing-source' else 9,name='FileNotFoundError' if label=='missing-source' else 'OSError')
  elif label=='producer-failure':assert run['exception']==dict(operation='producer',errno=None,name='RuntimeError')
  else:assert run['exception'] is None
  # Audit real observation paths without using producer helpers or hardcoded inode values.
  calls=run['syscalls'];assert calls and [c['seq'] for c in calls]==list(range(len(calls)))
  operations={c['operation'] for c in calls};assert {'open','write','lseek','read','fstat','stat','close'}<=operations
  if label in ['unlink','gap']:assert any(c['operation']=='unlink' and c['status']=='RETURNED' for c in calls)
  if label in ['replace','gap']:assert any(c['operation']=='replace' and c['status']=='RETURNED' for c in calls)
  if label=='gap':
   a=next(c['seq'] for c in calls if c['operation']=='unlink');b=next(c['seq'] for c in calls if c['operation']=='replace');assert any(a<c['seq']<b and c['operation']=='open' and c['status']=='OS_EXCEPTION' and c['errno']==2 for c in calls)
  if x['fsync']:assert sum(c['operation']=='fsync' and c['status']=='RETURNED' for c in calls)==2
  else:assert 'fsync' not in operations
  assert run['fd_numbers']['old']!=run['fd_numbers']['new'];assert all(type(v)==int and v>=0 for v in run['fd_numbers'].values())
 if literal and status=='OBSERVED':
  runs={v['label']:v for v in r['runs']};assert runs['unlink']['trace'][-1]['pathname']['status']==literal['unlink_path'];assert runs['replace']['trace'][-1]['pathname']['bytes']==literal['replace_path'];assert runs['gap']['trace'][1]['pathname']['status']==literal['gap_path'];assert all(row['old_fd'].get('bytes')==literal['old_fd'] for run in r['runs'] for row in run['trace'])
if __name__=='__main__':
 try:
  a=json.load(sys.stdin);check(a['result'],a['input'],a.get('literal'));print(json.dumps({'status':'passed'}))
 except Exception as e:print(json.dumps({'status':'failed','reason':type(e).__name__}));sys.exit(1)
