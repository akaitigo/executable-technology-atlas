#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Real owned loopback HTTP server and stdlib client; always close both."""
import hashlib
import http.client
import json
import platform
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
from client import evaluate

HERE=Path(__file__).resolve().parent


def digest(content):
    return "sha256:"+hashlib.sha256(content).hexdigest()


def run():
    cases=json.loads((HERE/"cases.json").read_text())
    contract=json.loads((HERE/"contract.json").read_text())
    lookup={"/cases/"+case["id"]:case for case in cases}
    server_events=[]
    class Handler(BaseHTTPRequestHandler):
        protocol_version="HTTP/1.1"
        server_version="LessonHTTP/1"
        def log_message(self,*args):
            pass
        def do_GET(self):
            case=lookup[self.path]
            body=case["body"].encode("utf-8")
            record={"path":self.path,"method":self.command,"headers":dict(self.headers.items()),
                    "intended_status":case["status"],"intended_body_digest":digest(body),"delay_seconds":case["delay_seconds"]}
            server_events.append(record)
            time.sleep(case["delay_seconds"])
            try:
                self.send_response(case["status"])
                self.send_header("Content-Type",case["content_type"])
                self.send_header("Content-Length",str(len(body)))
                self.send_header("Connection","close")
                self.end_headers()
                self.wfile.write(body)
                self.wfile.flush()
                record["write_result"]="completed"
            except (BrokenPipeError,ConnectionResetError):
                record["write_result"]="peer-closed"
            finally:
                self.close_connection=True
                record["finished"]=True
    server=HTTPServer(("127.0.0.1",0),Handler)
    port=server.server_address[1]
    thread=threading.Thread(target=server.serve_forever,kwargs={"poll_interval":0.01},name="owned-contract-http")
    thread.start()
    observations=[]
    try:
        for case in cases:
            timeout=0.1 if case["id"]=="timeout" else 2.0
            request={"method":"GET","path":"/cases/"+case["id"],"headers":{"Accept":"application/json","Connection":"close"},"body":None}
            connection=http.client.HTTPConnection("127.0.0.1",port,timeout=timeout)
            start=time.monotonic()
            response=None
            try:
                connection.request(request["method"],request["path"],headers=request["headers"])
                actual=connection.getresponse()
                body=actual.read(8193)
                if len(body)>8192:
                    raise ValueError("lesson body budget exceeded")
                response={"status":actual.status,"reason":actual.reason,"headers":dict(actual.getheaders()),
                          "body_text":body.decode("utf-8"),"body_hex":body.hex(),"body_bytes":len(body),"body_digest":digest(body)}
                decision=evaluate(actual.status,actual.getheader("Content-Type",""),body,contract)
                transport="response"
            except (socket.timeout,TimeoutError):
                transport="timeout"
                decision={"outcome":"timeout","accepted":False,"item":None,
                          "steps":[{"gate":"transport","verdict":"timeout","detail":"no complete response before socket timeout"}]}
            finally:
                connection.close()
            observations.append({"id":case["id"],"title":case["title"],"request":request,"response":response,
                "transport":transport,"socket_timeout_seconds":timeout,"elapsed_ms":round((time.monotonic()-start)*1000,3),
                "attempts":1,"retries":0,"decision":decision})
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
    assert not thread.is_alive(),"owned server thread still active"
    with socket.socket() as probe:
        probe.settimeout(0.2)
        refused=probe.connect_ex(("127.0.0.1",port))!=0
    assert refused,"owned server port still reachable"
    return {"subject":"api-integration-contracts","schema_version":1,
        "runtime":{"python_version":platform.python_version(),"os":platform.system(),"architecture":platform.machine(),
                   "client":"stdlib http.client.HTTPConnection","server":"stdlib http.server.HTTPServer", "http_version":"HTTP/1.1"},
        "input":{"contract":contract,"cases":cases,"request_schedule":"12 sequential GETs; no automatic retry",
                 "body_budget_bytes":8192,"timeout_design":"socket timeout 0.1s for delayed case; 2s otherwise; outer observation subprocess budget 15s"},
        "endpoint":{"host":"127.0.0.1","port":port,"binding":"dynamic owned loopback only"},
        "observations":observations,"server_events":server_events,
        "cleanup":{"server_closed":True,"thread_alive":thread.is_alive(),"port_connection_refused":refused},
        "scope":{"actual":"stdlib loopback HTTP requests/responses with fixed handwritten JSON contract",
                 "external_api":False,"real_auth":False,"tls":False,"full_http_spec":False,"general_json_schema":False,
                 "retry_correctness":False,"production_server":False}}


if __name__=="__main__":
    print(json.dumps(run(),ensure_ascii=False,sort_keys=True,indent=2))
