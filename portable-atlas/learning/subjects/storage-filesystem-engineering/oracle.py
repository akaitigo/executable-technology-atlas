"""Independent reader-state specification, no execution implementation import."""
import hashlib

def expected_summary(text):
 data=text.encode('ascii')
 return {'length':len(data),'sha256':hashlib.sha256(data).hexdigest(),'hex':data.hex()}
def expected_states(spec):
 old=spec['old'];new=spec['new'];prefix=new[:spec['cut']]
 if spec['mode']=='atomic-commit':return {'old_ready':(old,old,None),'candidate_empty':(old,old,''),'candidate_written':(old,old,new),'after_replace':(new,old,None)}
 if spec['mode']=='atomic-abort':return {'old_ready':(old,old,None),'candidate_empty':(old,old,''),'candidate_written':(old,old,prefix),'after_exception':(old,old,prefix)}
 return {'old_ready':(old,old,None),'after_truncate':('','',None),'partial_overwrite':(prefix,prefix,None),'after_exception':(prefix,prefix,None)}
def check(result):
 assert result['status']=='observed' and result['unexpected'] is None
 assert result['durability_proven'] is False
 spec=result['input'];states=expected_states(spec);es=result['events'];names=[e['event'] for e in es]
 def get(name):return next(e for e in es if e['event']==name)
 for name,(path,held,candidate) in states.items():
  e=get(name)
  assert e['path']==expected_summary(path),(name,'path')
  assert e['held_reader']==expected_summary(held),(name,'held')
  assert e['candidate']==(expected_summary(candidate) if candidate is not None else None),(name,'candidate')
  assert e['path_device']==e['held_device']
  if name=='after_replace':assert e['path_inode']!=e['held_inode'] and e['candidate_inode'] is None
  else:assert e['path_inode']==e['held_inode']
  if candidate is not None:assert e['candidate_device']==e['path_device'] and e['candidate_inode']!=e['path_inode']
 commit=spec['mode']=='atomic-commit'
 assert result['committed']==commit and result['injected_exception']==(not commit)
 assert ('replace_called' in names)==commit and ('replace_returned' in names)==commit
 if commit:
  assert names.index('candidate_written')<names.index('replace_called')<names.index('replace_returned')<names.index('after_replace')
  assert any(e['event']=='fsync_returned' and e['role']=='candidate' for e in es[:names.index('replace_called')])
  directory=[e for e in es if e.get('role')=='directory']
  assert directory[0]['event']=='fsync_called' and directory[1]['event'] in ('fsync_returned','fsync_failed')
 else:assert names.index('injected_exception')<names.index('after_exception')
 assert any(e['event']=='fsync_called' and e['role']=='initial-old' for e in es)
 assert result['cleanup']=={'held_reader_closed':True,'temp_removed':True}
 assert names[-2:]==['held_reader_closed','owned_temp_removed']
 assert not es[-1]['exists_after'] and es[-1]['existed_before']
 assert [e['seq'] for e in es]==list(range(len(es)))
 assert all(a['mono_ns']<=b['mono_ns'] for a,b in zip(es,es[1:]))
 return {'reader_states':len(states),'path_final_length':len((spec['new'] if commit else spec['old'] if spec['mode']=='atomic-abort' else spec['new'][:spec['cut']]).encode('ascii')),'held_final_is_old':(spec['mode']!='truncate-fail' or spec['new'][:spec['cut']]==spec['old']),'committed':commit,'cleanup':'owned temp removed / held reader closed','durability_proven':False}
