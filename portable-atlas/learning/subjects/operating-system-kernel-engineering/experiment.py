"""Actual POSIX child/pipe/signal experiment, bounded to one owned child at a time."""
import json, os, select, signal, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODES=('close','leak-release','leak-signal')
def validate(spec):
    if type(spec) is not dict or set(spec)!={'mode','payload','timeout_ms'}:
        raise ValueError('mode/payload/timeout_msだけを持つobjectが必要')
    if spec['mode'] not in MODES: raise ValueError('未対応mode')
    if type(spec['payload']) is not str or not spec['payload'].isascii() or len(spec['payload'])>512:
        raise ValueError('payloadは0..512文字ASCII')
    if type(spec['timeout_ms']) is not int or not 100<=spec['timeout_ms']<=500:
        raise ValueError('timeout_msはinteger 100..500（bool不可）')
    if spec['mode']=='leak-signal' and spec['payload']!='':
        raise ValueError('leak-signalは空payloadのみ（signalとreadのraceを教材契約から除外）')
    return spec

def execute(spec):
    validate(spec)
    parent=os.getpid(); events=[]; opened=set(); closed=[]; proc=None; ready=b''; rest=b''; err=b''
    child_events=[]; timed_out=False; cleanup_fallback=[]; failure=None; read_fd=write_fd=leak_fd=None
    start=time.monotonic_ns()
    def event(name,**fields):
        events.append(dict(actor='parent',event=name,seq=len(events),pid=parent,mono_ns=time.monotonic_ns(),wall_ns=time.time_ns(),**fields))
    def close_fd(fd,label):
        if fd in opened:
            event(label+'_begin',fd=fd)
            os.close(fd); opened.remove(fd);closed.append(fd);event(label,fd=fd)
    try:
        read_fd,write_fd=os.pipe();opened.update((read_fd,write_fd))
        event('pipe_created',read_fd=read_fd,write_fd=write_fd,parent_write_refs=1)
        if spec['mode']!='close':
            leak_fd=os.dup(write_fd);opened.add(leak_fd);event('write_duplicated',leak_fd=leak_fd,parent_write_refs=2)
        proc=subprocess.Popen([sys.executable,'-B',str(ROOT/'child.py'),str(read_fd)],pass_fds=(read_fd,),close_fds=True,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        event('child_spawned',child_pid=proc.pid,child_read_fd=read_fd,child_write_refs=0)
        close_fd(read_fd,'parent_read_closed')
        if not select.select([proc.stdout],[],[],3)[0]: raise TimeoutError('child ready timeout')
        ready=proc.stdout.readline()
        parsed=json.loads(ready)
        if parsed['event']!='ready' or parsed['pid']!=proc.pid: raise RuntimeError('invalid ready handshake')
        event('ready_received',child_pid=proc.pid)
        payload=spec['payload'].encode('ascii')
        if payload:
            offset=0
            while offset<len(payload): offset+=os.write(write_fd,payload[offset:])
            event('payload_written',bytes=len(payload),hex=payload.hex())
        close_fd(write_fd,'original_write_closed')
        event('writer_refs_checkpoint',parent_write_refs=int(leak_fd in opened),child_write_refs=0)
        wait_start=time.monotonic_ns()
        try:
            proc.wait(timeout=spec['timeout_ms']/1000)
            event('wait_completed',returncode=proc.returncode,elapsed_ns=time.monotonic_ns()-wait_start)
        except subprocess.TimeoutExpired:
            timed_out=True
            event('bounded_timeout',timeout_ms=spec['timeout_ms'],elapsed_ns=time.monotonic_ns()-wait_start,child_alive=proc.poll() is None,parent_write_refs=int(leak_fd in opened))
        if spec['mode']=='leak-release':
            close_fd(leak_fd,'leak_write_closed')
            proc.wait(timeout=3);event('child_reaped',returncode=proc.returncode)
        elif spec['mode']=='leak-signal':
            # Only our Popen child, never a caller-supplied PID or process group.
            proc.send_signal(signal.SIGTERM);event('sigterm_sent',child_pid=proc.pid,signal=int(signal.SIGTERM))
            proc.wait(timeout=3);event('child_reaped',returncode=proc.returncode)
            close_fd(leak_fd,'leak_write_closed')
        elif proc.poll() is None:
            raise TimeoutError('normal EOF wait timed out')
        rest,err=proc.communicate(timeout=3)
    except Exception as exc:
        failure={'type':type(exc).__name__,'message':str(exc).replace(str(ROOT),'MODULE')}
        event('experiment_failed',**failure)
    finally:
        for fd in list(opened): close_fd(fd,'cleanup_fd_closed')
        if proc is not None:
            if proc.poll() is None:
                cleanup_fallback.append('SIGTERM');proc.terminate()
                try: proc.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    cleanup_fallback.append('SIGKILL');proc.kill();proc.wait(timeout=3)
            if not rest and not err:
                remaining,stderr=proc.communicate(timeout=3);rest+=remaining;err+=stderr
            for stream in (proc.stdout,proc.stderr):
                if stream: stream.close()
            event('cleanup_complete',child_pid=proc.pid,reaped=proc.returncode is not None,parent_fds_open=len(opened),fallback=cleanup_fallback)
    raw_stdout=(ready+rest).decode('utf-8',errors='replace')
    for line in raw_stdout.splitlines():
        try: child_events.append(json.loads(line))
        except json.JSONDecodeError: failure={'type':'invalid_child_json','message':line}
    return {'status':'error' if failure else 'observed','input':spec,'parent_pid':parent,'child_pid':proc.pid if proc else None,'start_mono_ns':start,'end_mono_ns':time.monotonic_ns(),'parent_events':events,'child_events':child_events,'timeline':sorted(events+child_events,key=lambda e:e['wall_ns']),'raw_child_stdout':raw_stdout,'raw_child_stderr':err.decode('utf-8',errors='replace'),'bounded_timeout':timed_out,'returncode':proc.returncode if proc else None,'fds':{'parent_read':read_fd,'parent_write':write_fd,'parent_duplicate_write':leak_fd,'child_read':read_fd,'child_write':None},'cleanup':{'parent_open_fds':len(opened),'closed_parent_fds':closed,'child_reaped':proc is not None and proc.returncode is not None,'streams_closed':proc is not None and proc.stdout.closed and proc.stderr.closed,'fallback':cleanup_fallback},'failure':failure}
