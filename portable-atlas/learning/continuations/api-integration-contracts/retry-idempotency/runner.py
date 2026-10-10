"""Finite synthetic POST experiment. No external destinations."""
import argparse, datetime, hashlib, http.client, json, pathlib, platform, shutil, socket, sqlite3, tempfile, threading, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
ROOT = pathlib.Path(__file__).resolve().parent
CASES = ('no-key', 'same-key', 'key-conflict')
def canonical(body): return json.dumps(body, sort_keys=True, separators=(',', ':'))
def snapshot(path):
    with sqlite3.connect('file:' + str(path) + '?mode=ro&immutable=1', uri=True) as db:
        return {'orders': db.execute('SELECT id,sku,quantity FROM orders ORDER BY id').fetchall(), 'ledger': db.execute('SELECT key,request_hash,status,result,order_id FROM ledger ORDER BY key').fetchall(), 'integrity': db.execute('PRAGMA integrity_check').fetchone()[0]}
def run(case, artifact=None):
    if case not in CASES: raise ValueError('unsupported case')
    trace=[]; lock=threading.Lock(); start=time.monotonic_ns()
    def event(kind, **values):
        with lock: trace.append(dict(seq=len(trace)+1, utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), elapsed_ns=time.monotonic_ns()-start, kind=kind, **values))
    (ROOT/'observations'/'work').mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=ROOT/'observations'/'work') as tmp:
        path=pathlib.Path(tmp)/'orders.sqlite'
        with sqlite3.connect(path) as db:
            db.executescript('CREATE TABLE orders(id INTEGER PRIMARY KEY AUTOINCREMENT,sku TEXT NOT NULL,quantity INTEGER NOT NULL); CREATE TABLE ledger(key TEXT PRIMARY KEY,request_hash TEXT NOT NULL,status INTEGER NOT NULL,result TEXT NOT NULL,order_id INTEGER NOT NULL REFERENCES orders(id));')
        class Handler(BaseHTTPRequestHandler):
            protocol_version='HTTP/1.1'
            def log_message(self,*args): pass
            def do_POST(self):
                raw=self.rfile.read(int(self.headers['Content-Length'])); body=json.loads(raw); key=self.headers.get('Idempotency-Key')
                event('receive', method=self.command, path=self.path, body=body, bytes_hex=raw.hex(), key=key)
                digest=hashlib.sha256(canonical(body).encode()).hexdigest(); replay=False
                with sqlite3.connect(path) as db:
                    db.set_trace_callback(lambda sql:event('sql', statement=sql)); db.execute('PRAGMA foreign_keys=ON'); db.execute('BEGIN IMMEDIATE')
                    existing=db.execute('SELECT request_hash,status,result FROM ledger WHERE key=?',(key,)).fetchone() if key else None
                    if existing:
                        db.rollback()
                        if existing[0]!=digest: status=409; result=canonical({'error':'idempotency_key_body_conflict'})
                        else: status,result=existing[1:]; replay=True
                    else:
                        order_id=db.execute('INSERT INTO orders(sku,quantity) VALUES (?,?)',(body['sku'],body['quantity'])).lastrowid
                        status=201; result=canonical({'order_id':order_id,'sku':body['sku'],'quantity':body['quantity']})
                        if key: db.execute('INSERT INTO ledger VALUES (?,?,?,?,?)',(key,digest,status,result,order_id))
                        db.commit(); event('business_commit', order_id=order_id, ledger_written=bool(key), result=result)
                if self.headers.get('X-Lab-Drop-Response')=='once':
                    event('close_before_response'); self.close_connection=True; self.connection.shutdown(socket.SHUT_RDWR); self.connection.close(); return
                event('respond', status=status, result=result, replay=replay)
                data=result.encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(data))); self.send_header('Idempotent-Replayed',str(replay).lower()); self.end_headers(); self.wfile.write(data)
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler); server.daemon_threads=False
        port=server.server_port; thread=threading.Thread(target=server.serve_forever); thread.start()
        first={'sku':'demo-seat','quantity':1}; retry={'sku':'demo-seat','quantity':2 if case=='key-conflict' else 1}
        def send(body, drop):
            connection=http.client.HTTPConnection('127.0.0.1',port,timeout=2)
            headers={'Content-Type':'application/json'}
            if case!='no-key': headers['Idempotency-Key']='demo-request-1'
            if drop: headers['X-Lab-Drop-Response']='once'
            event('client_send', attempt=1 if drop else 2, body=body, headers=headers)
            try:
                connection.request('POST','/orders',body=canonical(body),headers=headers); response=connection.getresponse(); raw=response.read(8192)
                answer={'status':response.status,'body':json.loads(raw),'replay':response.getheader('Idempotent-Replayed')=='true'}; event('client_response', **answer); return answer
            except http.client.RemoteDisconnected as error:
                event('client_uncertain', exception=type(error).__name__, message=str(error)); return {'exception':type(error).__name__,'outcome':'unknown'}
            finally: connection.close()
        try:
            failure=send(first,True); after_first=snapshot(path); event('explicit_retry', maximum_retries=1); response=send(retry,False); after_retry=snapshot(path)
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=3)
        if artifact: shutil.copyfile(path,artifact)
        result={'case':case,'input':{'first':first,'retry':retry},'first_client':failure,'after_first':after_first,'retry_response':response,'after_retry':after_retry,'trace':trace,'environment':{'python':platform.python_version(),'sqlite':sqlite3.sqlite_version,'platform':platform.system()},'cleanup':{'port':port,'server_closed':True,'thread_joined':not thread.is_alive()}}
    result['cleanup']['temporary_database_removed']=not path.exists()
    return result
if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--case',choices=CASES,required=True); parser.add_argument('--inspect-evidence',action='store_true'); args=parser.parse_args()
    value=json.loads((ROOT/'observations'/'runs.json').read_text())[args.case] if args.inspect_evidence else run(args.case)
    print(json.dumps(value,ensure_ascii=False,indent=2))
