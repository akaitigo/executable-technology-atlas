# Atlas: executed as a new Python image by os.execve, using -I -S -c.
import errno
import fcntl
import json
import os
import sys

request = json.loads(sys.argv[1])
rows = {}
for label, fd in request['fds'].items():
    row = {'fd': fd}
    try:
        stat = os.fstat(fd)
        identity = [str(stat.st_dev), str(stat.st_ino)]
        row.update(identity=identity, cloexec=bool(fcntl.fcntl(fd, fcntl.F_GETFD) & fcntl.FD_CLOEXEC))
        if identity == request['target_identity']:
            row.update(status='target', bytes_hex=os.pread(fd, 8, 0).hex())
        else:
            row.update(status='different-target')
    except OSError as ex:
        row.update(status='EBADF' if ex.errno == errno.EBADF else 'os-error', errno=ex.errno, error_type=type(ex).__name__)
    rows[label] = row
closed = []
for label, row in rows.items():
    if row['status'] == 'target':
        os.close(row['fd'])
        closed.append(label)
message = {'phase':'child_after_exec', 'program':'atlas-fd-probe-v1', 'pid':os.getpid(), 'ppid':os.getppid(),
           'target_identity':request['target_identity'], 'fds':rows, 'explicitly_closed_target_labels':closed,
           'report_fd':request['report_fd']}
data = (json.dumps(message, sort_keys=True) + '\n').encode()
while data:
    amount = os.write(request['report_fd'], data)
    data = data[amount:]
os.close(request['report_fd'])
os._exit(0)
