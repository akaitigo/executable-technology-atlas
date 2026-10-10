# SPDX-License-Identifier: Apache-2.0
import sys
sys.dont_write_bytecode=True
import http.client,json,time,datetime,os
port=int(sys.argv[1]);which=sys.argv[2];id='qe-fast-01' if which=='fast' else 'qe-timeout-01';start=time.monotonic_ns();r=dict(request_id=id,pid=os.getpid(),timeout_s=2.0,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),start_monotonic_ns=start,client_received_status=None,client_received200=False,body=None)
c=http.client.HTTPConnection('127.0.0.1',port,timeout=2.0)
try:
 c.request('GET','/'+which+'?id='+id);response=c.getresponse();r['client_received_status']=response.status;body=response.read();r['body']=json.loads(body);r['client_received200']=response.status==200 and r['body']['request_id']==id;r['outcome']='RECEIVED_200' if r['client_received200'] else 'RESPONSE_OTHER'
except (TimeoutError,OSError) as e:r.update(outcome='CLIENT_TIMEOUT' if isinstance(e,TimeoutError) else 'CLIENT_TRANSPORT_ERROR',error_class=type(e).__name__,error_message=str(e))
finally:c.close();r.update(ended_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),end_monotonic_ns=time.monotonic_ns());r['observed_wait_ms']=(r['end_monotonic_ns']-start)/1e6
print(json.dumps(r,indent=2))
