"""Owned reader. Its write endpoints are not inherited (pass_fds includes only read_fd)."""
import json, os, signal, sys, time
fd=int(sys.argv[1])
seq=0
def emit(event, **fields):
    global seq
    print(json.dumps(dict(actor='child',event=event,seq=seq,pid=os.getpid(),ppid=os.getppid(),mono_ns=time.monotonic_ns(),wall_ns=time.time_ns(),**fields)),flush=True)
    seq+=1
emit('ready',read_fd=fd,write_end_inherited=False,sigterm_default=signal.getsignal(signal.SIGTERM)==signal.SIG_DFL)
try:
    while True:
        chunk=os.read(fd,256)
        if not chunk:
            emit('eof',read_return_bytes=0)
            break
        emit('data',hex=chunk.hex(),bytes=len(chunk))
finally:
    os.close(fd)
    emit('read_end_closed',read_fd=fd)
