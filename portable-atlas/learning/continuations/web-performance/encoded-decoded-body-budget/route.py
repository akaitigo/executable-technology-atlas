import json,sys
TARGETS={'body-budget':'producer.py','verify':'checker.py','compare':'index.html','sources':'SOURCES.md'}
def route(task):return dict(status='supported',target=TARGETS[task]) if task in TARGETS else dict(status='unsupported',reason='fixed same-origin body-size lesson only')
if __name__=='__main__':print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else 'body-budget')))
