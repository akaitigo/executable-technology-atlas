import json,sys
routes={'action':'README.md','compare':'EXPECTATIONS.md','sources':'SOURCES.md','verify':'checker.py'}
x=sys.argv[1] if len(sys.argv)>1 else 'action';print(json.dumps(dict(status='supported',path=routes[x]) if x in routes else dict(status='unsupported',request=x)));sys.exit(0 if x in routes else 2)
