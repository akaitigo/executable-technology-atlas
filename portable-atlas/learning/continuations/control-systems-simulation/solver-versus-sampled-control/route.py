"""Routes only this finite mathematical continuation."""
import json,sys
ROUTES={'sampling':'record.py','verify':'checker.py','timeline':'index.html','sources':'SOURCES.md'}
def route(topic):
 return dict(status='supported',target=ROUTES[topic]) if topic in ROUTES else dict(status='unsupported',reason='outside fixed mathematical fixture; see README limits')
if __name__=='__main__':
 r=route(sys.argv[1] if len(sys.argv)==2 else '');print(json.dumps(r));raise SystemExit(0 if r['status']=='supported' else 2)
