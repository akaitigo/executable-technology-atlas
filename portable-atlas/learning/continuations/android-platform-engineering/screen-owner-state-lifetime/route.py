import sys,json
TARGETS={'lifetime':'producer.py','verify':'checker.py','compare':'index.html','sources':'SOURCES.md'}
def route(task):return dict(status='supported',target=TARGETS[task]) if task in TARGETS else dict(status='unsupported',reason='finite Python owner model only')
if __name__=='__main__':print(json.dumps(route(sys.argv[1] if len(sys.argv)>1 else 'lifetime')))
