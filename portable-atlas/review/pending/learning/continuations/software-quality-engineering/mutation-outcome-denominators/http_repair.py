import sys
sys.dont_write_bytecode=True
import json,threading,urllib.request,datetime,importlib.util,hashlib
from pathlib import Path
from http.server import ThreadingHTTPServer
from model import evaluate
from verify import semantic
R=Path(__file__).resolve().parent
CASES=[('malformed','/evaluate?input=%7B'),('missing','/evaluate'),('blank','/evaluate?input='),('wrong_shape','/evaluate?input=%5B%5D'),('bad_status','/evaluate?input='+urllib.parse.quote(json.dumps(dict(report=[dict(id='m1',status='unknown')],fold=False)))),('valid','/evaluate?input='+urllib.parse.quote(json.dumps(dict(report=[dict(id='m1',status='Killed')],fold=False))))]
def capture(path,label):
 spec=importlib.util.spec_from_file_location('repair_'+label,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 server=ThreadingHTTPServer(('127.0.0.1',0),module.Handler);worker=threading.Thread(target=server.serve_forever,name='repair-http-'+label);worker.start();rows=[]
 try:
  for name,query in CASES:
   with urllib.request.urlopen('http://127.0.0.1:'+str(server.server_port)+query,timeout=3) as response:rows.append(dict(case=name,status=response.status,response=json.loads(response.read())))
 finally:
  server.shutdown();server.server_close();worker.join(3)
 assert not worker.is_alive() and server.socket.fileno()==-1
 return dict(rows=rows,cleanup=dict(listener_closed=True,worker_alive=False))
def validate(data):
 old=data['before'];new=data['after'];assert old['cleanup']==new['cleanup']==dict(listener_closed=True,worker_alive=False)
 assert [x['case'] for x in old['rows']]==[x[0] for x in CASES]==[x['case'] for x in new['rows']]
 expected=evaluate(None);keys=set(expected)|{'reason'}
 for prior,current in zip(old['rows'],new['rows']):
  assert prior['status']==current['status']==200
  if current['case'] in ('malformed','missing','blank'):
   assert set(prior['response'])=={'status','reason','greedy','optimal','subsets','greedy_trace'}
   r=current['response'];assert set(r)==keys and r['status']=='REFUSED_INPUT' and r['canonical'] is None and r['reported'] is None and r['classifications']==[] and r['inputs'] is None and r['reason']=='JSON input'
   assert r['runner_executed'] is False and r['timeout_executed'] is False and r['synthetic_report'] is True
   assert semantic(r)==dict(semantic(expected),reason='JSON input')
  else:assert semantic(prior['response'])==semantic(current['response'])
 assert new['rows'][-1]['response']['status']=='REPORT_AGGREGATED'
def main():
 p=R/'observations/repair-20261008'
 if sys.argv[1:]==['--record']:
  assert not (p/'http.json').exists()
  data=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),before=capture(p/'old-22/serve.py','old'),after=capture(R/'serve.py','new'),ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
  (p/'http.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');validate(data)
 else:
  assert not sys.argv[1:];data=json.loads((p/'http.json').read_text());validate(data)
  snapshot=json.loads((p/'snapshot.json').read_text());hashes=snapshot['hashes'];assert len(hashes)==22
  for n,h in hashes.items():assert hashlib.sha256((p/'old-22'/n).read_bytes()).hexdigest()==h
  assert hashlib.sha256(json.dumps(hashes,sort_keys=True,separators=(',',':')).encode()).hexdigest()==snapshot['digest']=='532fa7e9697f3d673d1dc5937c358c3ea9618c76c404da3a137a74c941780826'
 print('PASS: real HTTP before/after 6 cases; malformed/missing/blank canonical refusals; unchanged valid/semantic refusal; old22 reconstructed')
if __name__=='__main__':main()
