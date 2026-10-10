import json,sys
ROUTES={'draft':'record.py','verify':'checker.py','edit':'index.html','sources':'SOURCES.md'}
def route(t):return dict(status='supported',target=ROUTES[t]) if t in ROUTES else dict(status='unsupported',reason='outside vanilla JS 2-ID evidence; see README limits')
if __name__=='__main__':
 r=route(sys.argv[1] if len(sys.argv)==2 else '');print(json.dumps(r));sys.exit(0 if r['status']=='supported' else 2)
