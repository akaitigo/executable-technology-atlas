# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import json,subprocess,datetime,select
from pathlib import Path
from http.client import HTTPConnection
from domain import sender_domain,serialize
R=Path(__file__).resolve().parent
def utc():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def code(file):return "exec(compile(open('"+file+"').read(),'"+file+"','exec'))"
def evaluate(config):
 start=utc();out=dict(inputs=config,status='REFUSED_INPUT',started_utc=start,ended_utc=start,unit=None,attempts=[],receiver_process=None)
 if type(config) is not dict or set(config)!=set(['delay_ms','serializer','receiver']) or type(config['delay_ms']) is not int or config['delay_ms'] not in [1000,2000] or type(config['serializer']) is not str or config['serializer'] not in ['normal','seconds-string'] or type(config['receiver']) is not str or config['receiver'] not in ['strict','coerce']:return out
 fid='F'+str(config['delay_ms']);cmd=[sys.executable,'-B','-c',code('unit_worker.py'),fid,str(config['delay_ms']),config['receiver']];u=subprocess.run(cmd,cwd=str(R),capture_output=True,text=True,timeout=5);out['unit']=dict(command=['python3']+cmd[1:],exit_status=u.returncode,stdout=u.stdout,stderr=u.stderr,result=json.loads(u.stdout));domain=sender_domain(fid,config['delay_ms']);wire=serialize(domain,config['serializer']);out.update(fixture_id=fid,domain=domain,wire_utf8=wire.decode(),wire_hex=wire.hex())
 cmd=[sys.executable,'-B','-c',code('receiver_worker.py'),config['receiver']];p=subprocess.Popen(cmd,cwd=str(R),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);startup=None;tail='';error='';exit_status=None;attempts=[]
 try:
  if not select.select([p.stdout],[],[],5)[0]:raise RuntimeError('receiver startup deadline')
  line=p.stdout.readline();startup=json.loads(line)
  for number in [1,2]:
   a=dict(attempt=number,fixture_id=fid,started_utc=utc(),request_hex=wire.hex(),request_utf8=wire.decode(),request_headers={'Content-Type':'application/json','Content-Length':str(len(wire))},http_status=None,response_hex=None,response_utf8=None,response=None,outcome='TRANSPORT_FAILURE');connection=HTTPConnection('127.0.0.1',startup['port'],timeout=3)
   try:
    connection.request('POST','/delay',body=wire,headers=a['request_headers']);response=connection.getresponse();body=response.read();parsed=json.loads(body);a.update(http_status=response.status,response_hex=body.hex(),response_utf8=body.decode(),response=parsed,outcome='CONTRACT_REJECTED' if response.status==400 else 'MATCH' if parsed['accepted_delay_ms']==config['delay_ms'] else 'SEMANTIC_MISMATCH')
   except (OSError,ValueError) as e:a['error']=str(e)
   finally:connection.close();a['ended_utc']=utc();attempts.append(a)
  tail,error=p.communicate(timeout=6);exit_status=p.returncode
 except (ValueError,RuntimeError,subprocess.TimeoutExpired) as e:
  error=str(e)
  if p.poll() is None:p.terminate()
  rest,err=p.communicate(timeout=3);tail+=rest;error+='\n'+err;exit_status=p.returncode
 finally:
  if p.poll() is None:p.terminate();p.wait(timeout=3)
 try:final=json.loads(tail.strip()) if tail.strip() else None
 except ValueError:final=None
 out.update(status='HTTP_ATTEMPTS_RECORDED' if startup and final and len(final['records'])==2 and len(attempts)==2 else 'EXECUTION_INCOMPLETE',attempts=attempts,receiver_process=dict(command=['python3']+cmd[1:],startup=startup,final=final,exit_status=exit_status,stderr=error,final_stdout=tail,owned_child_closed=p.poll() is not None),ended_utc=utc());return out
