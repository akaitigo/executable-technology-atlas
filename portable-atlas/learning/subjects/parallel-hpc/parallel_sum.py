# SPDX-License-Identifier: Apache-2.0
"""Two owned spawn workers, private one-way pipes, bounded waits and cleanup."""
import math,multiprocessing as mp,os,time
from datetime import datetime,timezone
from multiprocessing.connection import wait
VERSION='finite-two-worker-sum-1'

def validate(f,policy):
    if not isinstance(f,dict):raise ValueError('fixture must be object')
    for key in ('start','stop'):
        if type(f.get(key)) is not int:raise ValueError(key+' must be exact integer')
    if not -10000<=f['start']<=f['stop']<=10000 or f['stop']-f['start']>10000:raise ValueError('bounded half-open range required')
    if policy not in ('balanced','drop-remainder'):raise ValueError('unknown partition policy')
    if f.get('behavior','normal') not in ('normal','worker-error','timeout'):raise ValueError('unknown worker behavior')

def partition(start,stop,policy):
    size=stop-start;mid=start+size//2
    return [[start,mid],[mid,stop if policy=='balanced' else mid+size//2]]

def worker(index,bounds,behavior,conn):
    started=time.perf_counter();pid=os.getpid()
    try:
        if behavior=='timeout':time.sleep(20)
        if behavior=='worker-error' and index==1:raise RuntimeError('authored worker1 failure')
        total=0
        for n in range(*bounds):total+=n
        conn.send(dict(index=index,pid=pid,bounds=bounds,status='OK',partial=total,count=bounds[1]-bounds[0],compute_elapsed_ms=(time.perf_counter()-started)*1000))
    except Exception as error:
        conn.send(dict(index=index,pid=pid,bounds=bounds,status='ERROR',partial=None,error=type(error).__name__+': '+str(error),compute_elapsed_ms=(time.perf_counter()-started)*1000))
    finally:conn.close()

def execute(f,policy='balanced'):
    validate(f,policy);bounds=partition(f['start'],f['stop'],policy);behavior=f.get('behavior','normal')
    started=time.perf_counter();events=[];processes=[];receivers=[];senders=[];messages={};status='OK';cleanup=[]
    def event(kind,**values):events.append(dict(event=kind,at_ms=(time.perf_counter()-started)*1000,**values))
    seq_start=time.perf_counter();seq=0
    for n in range(f['start'],f['stop']):seq+=n
    seq_ms=(time.perf_counter()-seq_start)*1000;event('sequential_finished',result=seq)
    timeout=.35 if behavior=='timeout' else 8.0
    ctx=mp.get_context('spawn');parallel_start=time.perf_counter()
    try:
        for i,span in enumerate(bounds):
            recv,send=ctx.Pipe(duplex=False);receivers.append(recv);senders.append(send)
            p=ctx.Process(target=worker,args=(i,span,behavior,send),name='atlas-parallel-hpc-'+str(i));processes.append(p)
            p.start();send.close();event('worker_started',index=i,pid=p.pid,bounds=span)
        pending=dict(zip(receivers,range(2)));deadline=time.perf_counter()+timeout
        while pending:
            remaining=deadline-time.perf_counter()
            if remaining<=0:status='TIMEOUT';event('deadline_expired',pending=list(pending.values()),timeout_s=timeout);break
            ready=wait(list(pending),timeout=remaining)
            if not ready:continue
            for conn in ready:
                index=pending.pop(conn)
                try:message=conn.recv()
                except EOFError:message=dict(index=index,pid=processes[index].pid,bounds=bounds[index],status='ERROR',partial=None,error='EOF without worker result')
                messages[index]=message;event('result_received',index=index,pid=message['pid'],status=message['status'],partial=message['partial'])
        if status!='TIMEOUT' and any(m['status']!='OK' for m in messages.values()):status='WORKER_ERROR'
    except BaseException:
        event('parent_exception_cleanup');raise
    finally:
        # Only Process objects created by this execution; never global active_children termination.
        for i,p in enumerate(processes):
            if p.pid is None:continue
            p.join(.2);reason='normal_exit_join'
            if p.is_alive():
                reason='deadline_cleanup' if status=='TIMEOUT' else 'join_grace_exceeded';event('terminate_owned',index=i,pid=p.pid,reason=reason)
                p.terminate();p.join(2)
            if p.is_alive():event('kill_owned',index=i,pid=p.pid,reason='terminate_join_exceeded');p.kill();p.join(2);reason+=';kill_fallback'
            row=dict(index=i,pid=p.pid,exit_code=p.exitcode,alive=p.is_alive(),reason=reason);cleanup.append(row);event('worker_joined',**row)
        for conn in receivers+senders:conn.close()
        if any(p.is_alive() for p in processes if p.pid is not None):raise RuntimeError('owned worker remained alive')
    parallel_ms=(time.perf_counter()-parallel_start)*1000
    partials=[messages.get(i,{}).get('partial') for i in range(2)]
    combined=sum(partials) if status=='OK' else None
    missing=list(range(bounds[1][1],f['stop']))
    comparison='MATCH' if combined==seq else ('MISMATCH' if status=='OK' else 'NO_RESULT')
    event('comparison',status=status,comparison=comparison,result=combined)
    return dict(id=f.get('id'),policy=policy,behavior=behavior,input=dict(start=f['start'],stop=f['stop']),partition=bounds,sequential_result=seq,partial_results=partials,parallel_result=combined,comparison=comparison,status=status,missing_values=missing,timeout_s=timeout,workers_requested=2,workers_started=len(cleanup),messages=[messages[i] for i in sorted(messages)],cleanup=cleanup,owned_remaining=sum(r['alive'] for r in cleanup),sequential_elapsed_ms=seq_ms,parallel_elapsed_ms=parallel_ms,elapsed_scope='observed local wall time including spawn/IPC/join; not speedup or throughput guarantee',executed_at_utc=datetime.now(timezone.utc).isoformat(),timeline=events)

def associativity():
    a,b,c=10**16,-10**16,1
    return dict(values=[a,b,c],integer_left=(a+b)+c,integer_right=a+(b+c),float_left=(float(a)+float(b))+float(c),float_right=float(a)+(float(b)+float(c)),exact_target=1,scope='Python unbounded integers; floating binary64 boundary witness only, no MPI run')
