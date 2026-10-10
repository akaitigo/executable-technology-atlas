#!/usr/bin/env python3
"""Atlas: mock-only cleanup checks; no fork, exec, file creation or child signal."""
import contextlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('atlas_fd_experiment',ROOT/'experiment.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def exercise(label,kill_error=False,close_error=False,unlink_error=False,never_reap=False):
    now=[0.0];reads=[0];closed=[];wait_calls=[]
    def select_read(*args):now[0]+=0.1;return ([21],[],[])
    def read(*args):
        reads[0]+=1
        if reads[0]==1:return b'{"phase":"child_after_fork","pid":424242}\n'
        raise TimeoutError('injected receive timeout')
    def wait(pid,option):
        wait_calls.append(option)
        return (0,0) if never_reap else (pid,9)
    def kill(*args):
        if kill_error:raise PermissionError('injected owned-child signal failure')
    def close(fd):
        closed.append(fd)
        if close_error and fd==20:raise OSError(5,'injected close failure')
    def unlink(*args):
        if unlink_error:raise OSError(5,'injected unlink failure')
    patches={'open':lambda *a:20,'write':lambda fd,data:len(data),'pipe':lambda:(21,22),
             'set_inheritable':lambda *a:None,'get_inheritable':lambda fd:True,'fork':lambda:424242,
             'read':read,'waitpid':wait,'kill':kill,'close':close}
    with contextlib.ExitStack() as stack:
        for name,func in patches.items():stack.enter_context(patch.object(m.os,name,func))
        stack.enter_context(patch.object(m.time,'monotonic',lambda:now[0]))
        stack.enter_context(patch.object(m.select,'select',select_read))
        stack.enter_context(patch.object(m.signal,'setitimer',lambda *a:0))
        stack.enter_context(patch.object(m,'identity',lambda fd:['1','2']))
        stack.enter_context(patch.object(m,'flags',lambda fd:1))
        stack.enter_context(patch.object(m,'set_cloexec',lambda fd,x:{'fd':fd,'observed':int(x)}))
        stack.enter_context(patch.object(m,'snapshot',lambda phase,*a:{'phase':phase,'pid':111,'fds':{}}))
        stack.enter_context(patch.object(m.Path,'unlink',unlink))
        r=m.one_case(('guarded_single',True,None),'/mock-owned', 'unused',10)
    checks={'failure_preserved':not r['complete'] and bool(r['errors']),
            'partial_pipe_kept':r['child_pipe_utf8'].endswith('\n') and len(r['partial_child_messages'])==1,
            'wait_only_nonblocking':bool(wait_calls) and all(x==m.os.WNOHANG for x in wait_calls),
            'closed_all_attempted':set(closed)=={20,21,22},
            'bounded_cleanup_wait':r['cleanup']['elapsed_seconds']<=1.11}
    if never_reap:checks['unreaped_is_not_success']=not r['cleanup']['child_reaped']
    if kill_error:checks['kill_error_recorded']=any(x['type']=='cleanup-kill-error' for x in r['errors'])
    if close_error:checks['close_error_recorded']=any(x['type']=='cleanup-fd-error' for x in r['errors'])
    if unlink_error:checks['unlink_error_recorded']=any(x['type']=='cleanup-unlink-error' for x in r['errors'])
    return {'id':label,'checks':checks,'pass':all(checks.values()),'saved_result':r}

results=[exercise('timeout-and-reap'),exercise('unreapable-owned-child',never_reap=True),exercise('cleanup-operation-errors',kill_error=True,close_error=True,unlink_error=True)]
print(json.dumps({'project':'Atlas','mock_only':True,'native_children_created':0,'results':results,'pass':all(x['pass'] for x in results)},indent=2))
raise SystemExit(0 if all(x['pass'] for x in results) else 1)
