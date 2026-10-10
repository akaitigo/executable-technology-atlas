"""Independent descriptor/path bookkeeping over recorded actual syscall args/results."""
def audit_run(run,x):
 ids=run['identities'];files={'old':'','new':''};paths={};fd={};offset={};allocated={};history=[]
 calls=run['syscalls'];assert [c['seq'] for c in calls]==list(range(len(calls)))
 def metadata(role):return dict(identity=ids[role],size=len(files[role]),nlink=sum(v==role for v in paths.values()))
 for c in calls:
  op,target,args,status,result=c['operation'],c['target'],c['args'],c['status'],c['result']
  assert status in ['RETURNED','OS_EXCEPTION']
  if status=='RETURNED':assert c['errno'] is None
  if op=='open':
   assert args[0] in ['live','prepared'];assert len(args) in [2,3]
   if status=='OS_EXCEPTION':assert args==['live',0] and 'live' not in paths and c['errno']==2 and result is None
   else:
    assert type(result)==int and result>=0 and result not in fd
    if len(args)==3:
     assert args[2]==384 and args[1]&512 and args[1]&2048 and args[1]&2 and args[0] not in paths
     role='old' if args[0]=='live' else 'new';assert role not in allocated;allocated[role]=result;paths[args[0]]=role
    else:assert args==['live',0] and 'live' in paths;role=paths['live']
    assert target==args[0];fd[result]=role;offset[result]=0
  elif op in ['write','read','lseek','fstat','close','fsync']:
   n=args[0];assert type(n)==int
   if status=='OS_EXCEPTION':
    assert op in ['read','fstat'] and n not in fd and c['errno']==9 and result is None
    expected='old' if target.startswith('old_fd') else 'new';assert n==allocated[expected]
    assert target==expected+'_fd_after_close' if op=='fstat' else target=='old_fd_closed'
   else:
    assert n in fd;role=fd[n]
    if target=='probe_fd':assert op in ['read','lseek','fstat','close']
    else:assert target==role+'_fd'
    if op=='write':
     assert len(args)==2 and type(args[1])==str and type(result)==int and 0<=result<=len(args[1]);assert result>0 or not args[1]
     pos=offset[n];files[role]=files[role][:pos]+args[1][:result]+files[role][pos+result:];offset[n]+=result
    elif op=='read':
     assert len(args)==2 and args[1] in [1,64] and type(result)==str and len(result)<=args[1];remaining=files[role][offset[n]:]
     assert result==remaining[:len(result)] and (bool(result) or not remaining);offset[n]+=len(result)
    elif op=='lseek':
     assert args[1:]==[0,0] or args[1:]==[0,1]
     if args[2]==0:offset[n]=0
     assert result==offset[n]
    elif op=='fstat':assert result==metadata(role)
    elif op=='close':assert len(args)==1 and result is None;del fd[n];del offset[n]
    elif op=='fsync':assert len(args)==1 and result is None and x['fsync']
  elif op=='stat':
   assert len(args)==1 and args[0] in ['live','prepared'] and target==args[0]
   if status=='OS_EXCEPTION':assert args[0] not in paths and c['errno']==2 and result is None
   else:assert result==metadata(paths[args[0]])
  elif op=='unlink':assert status=='RETURNED' and args==['live'] and target=='live' and result is None;del paths['live']
  elif op=='replace':
   assert len(args)==2 and args[1]=='live' and args[0] in ['prepared','missing'] and target==args[0]+'->live'
   if status=='OS_EXCEPTION':assert args[0]=='missing' and args[0] not in paths and c['errno']==2 and result is None
   else:assert result is None and args[0]=='prepared';paths['live']=paths.pop('prepared')
  else:raise AssertionError('unknown syscall')
  history.append(dict(fd=dict(fd),offset=dict(offset),paths=dict(paths),files=dict(files)))
 assert allocated==run['fd_numbers'];assert files=={'old':x['old_payload'],'new':x['new_payload']};assert fd=={}
 # Every owned/probe close is immediately checked (owned) or bound to the pathname row (probe).
 for i,c in enumerate(calls):
  if c['operation']=='close' and c['target'] in ['old_fd','new_fd']:
   follow=calls[i+1];assert follow['operation']=='fstat' and follow['target']==c['target']+'_after_close' and follow['args']==c['args'] and follow['status']=='OS_EXCEPTION' and follow['errno']==9
 if run['label']=='closed-fd':
  read=next(c for c in calls if c['target']=='old_fd_closed');i=read['seq'];assert calls[i-1]['target']=='old_fd_after_close' and calls[i-2]['operation']=='close' and calls[i-2]['target']=='old_fd';assert read['args']==[allocated['old'],1] and read['errno']==9
 # Actual syscall spans must reconstruct all rendered row values, with descriptor reuse tracked above.
 end=0
 for row in run['trace']:
  start,stop=row['syscall_span'];assert type(start)==int and type(stop)==int and end<=start<stop<=len(calls);end=stop;span=calls[start:stop]
  for name in ['old','new']:
   got=row[name+'_fd'];part=[c for c in span if c['target']==name+'_fd']
   if got['state']=='CLOSED':assert not part and allocated[name] not in history[start-1]['fd'];continue
   assert part[0]['operation']=='lseek' and part[0]['args']==[allocated[name],0,0] and part[0]['result']==got['seek_result']
   reads=[c for c in part if c['operation']=='read'];assert len(reads)==got['read_calls']+1 and reads[-1]['args'][1]==1 and reads[-1]['result']==got['eof']=='';assert ''.join(c['result'] for c in reads)==got['bytes']
   assert part[-2]['operation']=='lseek' and part[-2]['args']==[allocated[name],0,1] and part[-2]['result']==got['offset_after']
   assert part[-1]['operation']=='fstat' and part[-1]['result']==dict(identity=got['identity'],size=got['size'],nlink=got['nlink'])
  live=[c for c in span if c['target']=='live'];got=row['pathname']
  if got['status']=='ENOENT':assert [(c['operation'],c['status'],c['errno']) for c in live]==[('stat','OS_EXCEPTION',2),('open','OS_EXCEPTION',2)]
  else:
   assert [c['operation'] for c in live]==['stat','open'];assert live[0]['result']['identity']==got['stat_identity'];probe=live[1]['result'];part=[c for c in span if c['target']=='probe_fd'];assert all(c['args'][0]==probe for c in part);assert ''.join(c['result'] for c in part if c['operation']=='read')==got['bytes'];fstat=next(c for c in part if c['operation']=='fstat');assert fstat['result']['identity']==got['identity'] and fstat['result']['nlink']==got['nlink'];assert part[-1]['operation']=='close' and probe not in history[part[-1]['seq']]['fd'] and got['closed_after_probe']
  prepared=span[-1];assert prepared['operation']=='stat' and prepared['target']=='prepared';got=row['prepared_path'];assert (prepared['result']['identity'] if prepared['status']=='RETURNED' else None)==got['identity'];assert prepared['errno']==got['errno']
 for name in ['old','new']:
  final=next(c for c in reversed(calls) if c['target']==name+'_fd_after_close');assert final['status']=='OS_EXCEPTION' and final['errno']==9 and final['args']==[allocated[name]] and final['seq']>=end
 return True

def audit(r,x):
 for run in r['runs']:audit_run(run,x)
