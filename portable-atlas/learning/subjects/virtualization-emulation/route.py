import argparse,json
ROUTES={'emulator':'runner.py','verify':'checker.py','register-memory':'index.html','sources':'SOURCES.md'}
def route(topic):return {'status':'supported','target':ROUTES[topic]} if topic in ROUTES else {'status':'unsupported','target':'COVERAGE.md','reason':'hypervisor/VM boot/isolation/JIT/devices/migration等は今回未教材'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('topic');a=p.parse_args();r=route(a.topic);print(json.dumps(r,ensure_ascii=False));raise SystemExit(0 if r['status']=='supported' else 2)
