"""Real bounded UDP loopback. No oracle imports, threads, retries or external names."""
import json
import platform
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from policies import compare

ROOT = Path(__file__).resolve().parent
TIMEOUT = 0.3

def utc():
    return datetime.now(timezone.utc).isoformat()

def observe(case):
    owned = []
    result = {'id': case['id'], 'started_at': utc(), 'events': [], 'status': 'running'}
    def event(kind, **fields):
        result['events'].append({'at': utc(), 'kind': kind, **fields})
    try:
        for role in ('receiver', 'sender'):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            owned.append((role, sock))
            sock.settimeout(TIMEOUT)
            sock.bind(('127.0.0.1', 0))
            result[role] = list(sock.getsockname())
            event('bind', role=role, address=result[role], timeout_seconds=TIMEOUT)
        receiver, sender = owned[0][1], owned[1][1]
        # Send both before reading, without relying on a background thread.
        for number, raw in enumerate(case['sent_hex'], 1):
            data = bytes.fromhex(raw)
            event('sendto-call', number=number, payload_hex=raw, byte_count=len(data), destination=result['receiver'])
            returned = sender.sendto(data, tuple(result['receiver']))
            event('sendto-return', number=number, returned_bytes=returned, business_ack=False)
        for number, width in enumerate(case['recv_widths'], 1):
            start = time.monotonic_ns()
            event('recvfrom-call', number=number, bufsize=width, flags=0)
            try:
                data, address = receiver.recvfrom(width)
                event('recvfrom-return', number=number, payload_hex=data.hex(), byte_count=len(data), sender=list(address), elapsed_ns=time.monotonic_ns()-start)
            except socket.timeout as error:
                event('recvfrom-timeout', number=number, exception=type(error).__name__, message=str(error), elapsed_ns=time.monotonic_ns()-start)
        result['status'] = 'observed'
    except Exception as error:
        result['status'] = 'failed'
        result['failure'] = {'at': utc(), 'type': type(error).__name__, 'message': str(error), 'errno': getattr(error, 'errno', None)}
    finally:
        for role, sock in reversed(owned):
            sock.close()
            event('close', role=role, fileno_after_close=sock.fileno())
        result['cleanup'] = {'created': len(owned), 'closed': sum(sock.fileno()==-1 for _,sock in owned), 'open_owned_sockets': sum(sock.fileno()!=-1 for _,sock in owned), 'owned_threads': 0, 'method': 'same-thread finite calls; finally close'}
        result['ended_at'] = utc()
        result['consumer_prototypes'] = compare(result['events'])
    return result

def main():
    config = json.loads((ROOT/'contracts.json').read_text())
    # Only literal inputs and widths enter observe(); expected bytes never do.
    cases = [observe({key: item[key] for key in ('id', 'sent_hex', 'recv_widths')}) for item in config['cases']]
    print(json.dumps({'started_at': cases[0]['started_at'], 'ended_at': utc(), 'environment': {'python': platform.python_version(), 'os': platform.system(), 'release': platform.release(), 'machine': platform.machine(), 'api': 'AF_INET / SOCK_DGRAM / recvfrom(flags=0)', 'dependencies': 'stdlib'}, 'timeout_seconds': TIMEOUT, 'attempts': 1, 'retries': 0, 'cases': cases}, ensure_ascii=False))
    return 0 if all(case['status']=='observed' for case in cases) else 1

if __name__ == '__main__':
    raise SystemExit(main())
