"""Finite continuation routing, no resource provisioning."""
import json,sys
ROUTES={'locking':'experiment.py','verify':'checker.py','timeline':'index.html','sources':'SOURCES.md'}
def route(topic):
 if topic in ROUTES:return dict(status='supported',target=ROUTES[topic])
 return dict(status='unsupported',reason='outside measured Mac owned-process continuation; see README limits')
if __name__=='__main__':
 r=route(sys.argv[1] if len(sys.argv)==2 else '');print(json.dumps(r));raise SystemExit(0 if r['status']=='supported' else 2)
