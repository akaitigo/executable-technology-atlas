import argparse,json
ROUTES={'quoting':'runner.py','verify':'checker.py','character-trace':'index.html','sources':'SOURCES.md'}
def route(topic):return {'status':'supported','target':ROUTES[topic]} if topic in ROUTES else {'status':'unsupported','reason':'finite argument-tail quoting subset model only','next':'COVERAGE.md'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('topic');a=p.parse_args();r=route(a.topic);print(json.dumps(r));raise SystemExit(0 if r['status']=='supported' else 2)
