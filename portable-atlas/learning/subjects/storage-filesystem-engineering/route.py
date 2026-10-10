import argparse,json
ROUTES={'replace':'runner.py','verify':'checker.py','timeline':'index.html','sources':'SOURCES.md'}
def route(topic):return {'status':'supported','target':ROUTES[topic]} if topic in ROUTES else {'status':'unsupported','target':'COVERAGE.md','reason':'block-CoW/crash durability/RAID/fs repair/kernel storage driver等は今回未教材'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('topic');a=p.parse_args();r=route(a.topic);print(json.dumps(r,ensure_ascii=False));raise SystemExit(0 if r['status']=='supported' else 2)
