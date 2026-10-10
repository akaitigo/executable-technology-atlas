"""Only fixed circular-footprint mathematical lesson routes."""
import sys,json
R={'footprint':'record.py','verify':'checker.py','diagram':'index.html','sources':'SOURCES.md'}
def route(topic):return dict(status='supported',target=R[topic]) if topic in R else dict(status='unsupported',reason='outside fixed geometry; see README limits')
if __name__=='__main__':
 r=route(sys.argv[1] if len(sys.argv)==2 else '');print(json.dumps(r));raise SystemExit(0 if r['status']=='supported' else 2)
