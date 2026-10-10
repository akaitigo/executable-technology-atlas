import sys
sys.dont_write_bytecode=True
import socket,copy,platform,datetime
from framing import validate,classify,reply

def observe(f,mode,width,probe=None):
 validate(f,mode,width)
 if probe not in (None,'timeout','closed_recv'):raise ValueError('probe')
 states={n:dict(tx='open',rx='open') for n in 'AB'};trace=[];owned=[]
 row=dict(fixture=f['id'],mode=mode,width=width,probe=probe,execution_status='passed',protocol_outcome='undetermined',request_received_hex='',response_sent_hex='',response_received_hex='',request_decision=None,trace=trace,errors=[])
 def event(end,api,result,**kw):trace.append(dict(endpoint=end,api=api,result=result,states=copy.deepcopy(states),**kw))
 def read(sock,end):
  chunks=[]
  for _ in range(130):
   b=sock.recv(width)
   if not b:states[end]['rx']='eof';event(end,'recv','eof',bytes=0,hex='');return chunks
   chunks.append(b);event(end,'recv','data',bytes=len(b),hex=b.hex())
   if sum(map(len,chunks))>128:raise RuntimeError('read byte limit')
  raise RuntimeError('recv call limit')
 endpoint='pair';api='socketpair'
 try:
  a,b=socket.socketpair(socket.AF_UNIX,socket.SOCK_STREAM);owned=[a,b];event('pair','socketpair','connected',family='AF_UNIX',type='SOCK_STREAM')
  for endpoint,sock in zip('AB',owned):sock.settimeout(2);event(endpoint,'settimeout','ok',seconds=2)
  if probe=='timeout':
   endpoint='B';api='recv';b.settimeout(0.02);event('B','settimeout','ok',seconds=0.02);b.recv(width)
   raise AssertionError('timeout probe unexpectedly returned')
  if probe=='closed_recv':
   endpoint='B';api='close';b.close();states['B']=dict(tx='closed',rx='closed');event('B','close','ok');api='recv';b.recv(width)
   raise AssertionError('closed recv unexpectedly returned')
  endpoint='A';api='sendall';wire=bytes.fromhex(f['wire']);a.sendall(wire);event('A','sendall','ok',bytes=len(wire),hex=wire.hex())
  api='shutdown';a.shutdown(socket.SHUT_WR);states['A']['tx']='shut_wr';event('A','shutdown','ok',how='SHUT_WR')
  endpoint='B';api='recv';chunks=read(b,'B');row['request_received_hex']=b''.join(chunks).hex()
  api='classify';decision=classify(chunks);row['request_decision']=decision;event('B','classify','decision',kind=decision['kind'])
  if mode=='normal':
   response=reply(decision);api='sendall';b.sendall(response);row['response_sent_hex']=response.hex();event('B','sendall','ok',bytes=len(response),hex=response.hex())
   row['protocol_outcome']='normal' if decision['kind']=='complete' else 'refusal'
  else:event('B','fault','reply_omitted');row['protocol_outcome']='missing_response'
  api='shutdown';b.shutdown(socket.SHUT_WR);states['B']['tx']='shut_wr';event('B','shutdown','ok',how='SHUT_WR')
  endpoint='A';api='recv';row['response_received_hex']=b''.join(read(a,'A')).hex()
 except Exception as exc:
  row['execution_status']='timeout' if isinstance(exc,socket.timeout) else 'execution_failure'
  row['errors'].append(dict(endpoint=endpoint,api=api,type=type(exc).__name__,message=str(exc),errno=getattr(exc,'errno',None)))
  event(endpoint,api,'exception',type=type(exc).__name__,errno=getattr(exc,'errno',None))
 finally:
  for endpoint,sock in zip('AB',owned):
   sock.close();states[endpoint]=dict(tx='closed',rx='closed');event(endpoint,'close','ok')
  row['closed_filenos']=[s.fileno() for s in owned];row['owned_count']=len(owned)
 return row
def environment():return dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),python=platform.python_version(),platform=platform.system(),transport='AF_UNIX SOCK_STREAM socketpair; no bind/network; one calling thread')
