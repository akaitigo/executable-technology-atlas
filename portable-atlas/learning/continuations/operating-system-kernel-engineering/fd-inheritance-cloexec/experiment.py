#!/usr/bin/env python3
"""Atlas: four finite fork/exec cases; --record is the only measurement entry."""
import argparse
import datetime
import errno
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import select
import signal
import sys
import tempfile
import time
import traceback

ROOT = Path(__file__).resolve().parent
PAYLOAD = b'ATLAS-FD'
# Inputs are explicit; verification uses the separately frozen expected.json.
CASES = [('guarded_single', True, None), ('unguarded_single', False, None),
         ('dup_original_guarded', True, False), ('dup_duplicate_guarded', False, True)]

def identity(fd):
    s = os.fstat(fd)
    return [str(s.st_dev), str(s.st_ino)]

def flags(fd):
    return fcntl.fcntl(fd, fcntl.F_GETFD)

def set_cloexec(fd, value):
    before = flags(fd)
    after = before | fcntl.FD_CLOEXEC if value else before & ~fcntl.FD_CLOEXEC
    fcntl.fcntl(fd, fcntl.F_SETFD, after)
    return {'fd':fd, 'before':before, 'requested':after, 'observed':flags(fd)}

def snapshot(phase, fds, target):
    rows = {}
    for label, fd in fds.items():
        row = {'fd':fd}
        try:
            actual = identity(fd)
            row.update(identity=actual, cloexec=bool(flags(fd) & fcntl.FD_CLOEXEC))
            row['status'] = 'target' if actual == target else 'different-target'
            if row['status'] == 'target':row['bytes_hex'] = os.pread(fd, len(PAYLOAD), 0).hex()
        except OSError as ex:
            row.update(status='EBADF' if ex.errno==errno.EBADF else 'os-error', errno=ex.errno, error_type=type(ex).__name__)
        rows[label] = row
    return {'phase':phase,'program':'atlas-fd-experiment-v1','pid':os.getpid(),'ppid':os.getppid(),'target_identity':target,'fds':rows}

def send(fd, value):
    data = (json.dumps(value, sort_keys=True)+'\n').encode()
    while data:
        sent = os.write(fd,data)
        data = data[sent:]

def one_case(spec, directory, exec_code, batch_deadline):
    name, original_flag, duplicate_flag = spec
    result = {'id':name,'phases':[],'setup':[],'errors':[],'cleanup':{},'complete':False,'child_pipe_utf8':'','partial_child_messages':[]}
    owned = set();child = None;reaped = False;report_r = None
    filename = Path(directory)/name
    try:
        original = os.open(filename, os.O_CREAT|os.O_EXCL|os.O_RDWR, 0o600);owned.add(original)
        written = os.write(original,PAYLOAD)
        result['payload_written_bytes'] = written
        if written != len(PAYLOAD):raise RuntimeError('short payload write')
        target = identity(original);result['target_identity'] = target
        fds = {'original':original}
        result['setup'].append({'operation':'os.open','fd':original,'initial_cloexec':bool(flags(original)&fcntl.FD_CLOEXEC)})
        result['setup'].append({'operation':'set original CLOEXEC',**set_cloexec(original,original_flag)})
        if duplicate_flag is not None:
            duplicate = os.dup(original);owned.add(duplicate);fds['duplicate']=duplicate
            result['setup'].append({'operation':'os.dup','from_fd':original,'fd':duplicate,'initial_cloexec':bool(flags(duplicate)&fcntl.FD_CLOEXEC),'identity':identity(duplicate)})
            result['setup'].append({'operation':'set duplicate CLOEXEC',**set_cloexec(duplicate,duplicate_flag)})
        report_r,report_w=os.pipe();owned.update([report_r,report_w]);os.set_inheritable(report_w,True)
        result['control_pipe']={'read_fd':report_r,'write_fd':report_w,'write_inheritable':os.get_inheritable(report_w),'not_measured_target':report_w not in fds.values() and report_r not in fds.values()}
        request={'fds':fds,'target_identity':target,'report_fd':report_w}
        argv=[sys.executable,'-I','-S','-c',exec_code,json.dumps(request,sort_keys=True)]
        result['exec_call']={'executable':sys.executable,'argv':argv,'environment':{'PYTHONDONTWRITEBYTECODE':'1'}}
        result['phases'].append(snapshot('parent_before_fork',fds,target))
        child=os.fork()
        if child==0:
            try:
                os.close(report_r)
                send(report_w,snapshot('child_after_fork',fds,target))
                os.execve(sys.executable,argv,{'PYTHONDONTWRITEBYTECODE':'1'})
            except BaseException as ex:
                try:send(report_w,{'phase':'child_execution_failure','pid':os.getpid(),'error_type':type(ex).__name__,'message':str(ex),'errno':getattr(ex,'errno',None)})
                finally:os._exit(70)
        result['fork_returned_child_pid']=child
        os.close(report_w);owned.remove(report_w);result['control_pipe']['parent_write_end_closed']=True
        deadline=min(time.monotonic()+2,batch_deadline)
        chunks=[];total=0
        while True:
            remaining=deadline-time.monotonic()
            if remaining<=0:raise TimeoutError('child report deadline exceeded')
            ready,_,_=select.select([report_r],[],[],remaining)
            if not ready:raise TimeoutError('child report timeout')
            data=os.read(report_r,8192)
            if not data:break
            chunks.append(data);total+=len(data)
            result['child_pipe_utf8']=b''.join(chunks).decode(errors='replace')
            result['received_bytes']=total
            if total>32768:raise RuntimeError('child report exceeds fixed budget')
        raw=b''.join(chunks);result['child_pipe_utf8']=raw.decode()
        result['phases'].extend(json.loads(line) for line in raw.decode().splitlines())
        while True:
            pid,status=os.waitpid(child,os.WNOHANG)
            if pid==child:
                reaped=True;result['wait']={'pid':pid,'raw_status':status,'exited':os.WIFEXITED(status),'exit_code':os.WEXITSTATUS(status) if os.WIFEXITED(status) else None,'signaled':os.WIFSIGNALED(status)};break
            if time.monotonic()>=deadline:raise TimeoutError('child wait deadline exceeded')
            select.select([],[],[],min(0.01,deadline-time.monotonic()))
        if result['wait']['exit_code']!=0:raise RuntimeError('exec child failed')
        result['phases'].append(snapshot('parent_after_wait',fds,target))
        result['complete']=True
    except BaseException as ex:
        result['errors'].append({'type':type(ex).__name__,'message':str(ex),'errno':getattr(ex,'errno',None),'traceback':traceback.format_exc()})
    finally:
        # Observation deadline must not interrupt cleanup and discard this case.
        signal.setitimer(signal.ITIMER_REAL, 0)
        for line in result['child_pipe_utf8'].splitlines():
            try:result['partial_child_messages'].append(json.loads(line))
            except (ValueError,TypeError):pass
        cleanup_started=time.monotonic()
        if child and not reaped:
            try:
                os.kill(child,signal.SIGKILL);result['cleanup']['child_killed_on_failure']=True
            except ProcessLookupError:result['cleanup']['child_already_exited']=True
            except BaseException as ex:
                result['errors'].append({'type':'cleanup-kill-error','detail':type(ex).__name__,'message':str(ex)})
            while time.monotonic()-cleanup_started<1:
                try:
                    pid,status=os.waitpid(child,os.WNOHANG)
                    if pid==child:
                        reaped=True;result['cleanup']['failure_wait']={'pid':pid,'raw_status':status};break
                    select.select([],[],[],min(0.01,max(0,1-(time.monotonic()-cleanup_started))))
                except BaseException as ex:
                    result['errors'].append({'type':'cleanup-wait-error','detail':type(ex).__name__,'message':str(ex)});break
            if not reaped:
                result['errors'].append({'type':'cleanup-wait-timeout','message':'owned child could not be reaped within one second; no next case'})
        result['cleanup']['child_reaped']=reaped if child else True
        result['cleanup']['wait_grace_seconds']=1
        closed=[]
        for fd in sorted(owned):
            try:os.close(fd);closed.append(fd)
            except BaseException as ex:
                result['errors'].append({'type':'cleanup-fd-error','fd':fd,'detail':type(ex).__name__,'errno':getattr(ex,'errno',None)})
        result['cleanup']['parent_closed_fds']=closed
        result['cleanup']['all_parent_owned_fds_closed']=len(closed)==len(owned)
        result['cleanup']['owned_target_unlinked']=False
        try:
            filename.unlink();result['cleanup']['owned_target_unlinked']=True
        except FileNotFoundError:result['cleanup']['owned_target_unlinked']=True
        except BaseException as ex:
            result['errors'].append({'type':'cleanup-unlink-error','detail':type(ex).__name__,'message':str(ex)})
        result['cleanup']['elapsed_seconds']=time.monotonic()-cleanup_started
        if result['errors'] or not result['cleanup']['child_reaped']:
            result['complete']=False
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--record',action='store_true');args=parser.parse_args()
    if not args.record:
        print('Atlas: use --record only for an authorized new measurement. Read observations for saved results.');return 0
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output=ROOT/'observations'/('attempt-'+stamp);output.mkdir()
    inputs=['CONTRACT.md','expected.json','sources.json','experiment.py','probe.py','verify.py']
    result={'project':'Atlas','schema_version':1,'started_at':stamp,'environment':{'python':sys.version,'executable':sys.executable,'platform':platform.platform(),'kernel_release':platform.release(),'cpu_count':os.cpu_count()},'input_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in inputs},'cases':[],'errors':[],'collection_complete':False,'cleanup':{},'limits':{'max_concurrent_children':1,'child_timeout_seconds':2,'batch_timeout_seconds':10,'cleanup_wait_grace_seconds':1,'payload_bytes_per_case':8},'max_concurrent_children_observed':0}
    def alarm(_sig,_frame):raise TimeoutError('10 second batch deadline exceeded')
    original_handler=signal.signal(signal.SIGALRM,alarm)
    started=time.monotonic();temporary=None
    try:
        current=os.getpriority(os.PRIO_PROCESS,0)
        if current<10:os.nice(10-current)
        result['nice']=os.getpriority(os.PRIO_PROCESS,0)
        if result['nice']<10:raise RuntimeError('required low priority was not applied')
        code=(ROOT/'probe.py').read_text()
        with tempfile.TemporaryDirectory(prefix='atlas-fd-cloexec-') as temp:
            temporary=temp
            for spec in CASES:
                remaining=started+10-time.monotonic()
                if remaining<=0:raise TimeoutError('batch observation deadline exceeded')
                signal.setitimer(signal.ITIMER_REAL,remaining)
                case=one_case(spec,temp,code,started+10);result['cases'].append(case)
                if case.get('fork_returned_child_pid'):result['max_concurrent_children_observed']=1
                if not case['complete']:break
        result['collection_complete']=len(result['cases'])==4 and all(c['complete'] for c in result['cases'])
    except BaseException as ex:
        result['errors'].append({'type':type(ex).__name__,'message':str(ex),'errno':getattr(ex,'errno',None),'traceback':traceback.format_exc()})
    finally:
        signal.setitimer(signal.ITIMER_REAL,0);signal.signal(signal.SIGALRM,original_handler)
        result['cleanup']['temporary_directory_removed']=temporary is None or not Path(temporary).exists()
        result['cleanup']['temporary_directory_created']=temporary is not None
        result['elapsed_seconds']=time.monotonic()-started
        result['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        (output/'run.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps(result,ensure_ascii=False,sort_keys=True),flush=True)
        print(json.dumps({'project':'Atlas','saved_run':str((output/'run.json').relative_to(ROOT)),'collection_complete':result['collection_complete']}),flush=True)
    return 0 if result['collection_complete'] and not result['errors'] else 1
if __name__=='__main__':raise SystemExit(main())
