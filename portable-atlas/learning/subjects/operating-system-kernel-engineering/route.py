import argparse,json
ROUTES={'pipe':'runner.py','verify':'checker.py','fd-diagram':'index.html','sources':'SOURCES.md'}
def route(topic):
 return {'status':'supported','target':ROUTES[topic]} if topic in ROUTES else {'status':'unsupported','target':'COVERAGE.md','reason':'kernel改造/VM/scheduler/mm/filesystem/driver等は今回未教材'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('topic');a=p.parse_args();r=route(a.topic);print(json.dumps(r,ensure_ascii=False));raise SystemExit(0 if r['status']=='supported' else 2)
