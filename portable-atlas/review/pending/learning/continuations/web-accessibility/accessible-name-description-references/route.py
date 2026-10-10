import sys,json
r={'names':'README.md','references':'EXPECTATIONS.md','sources':'SOURCES.md','verify':'checker.py'}
x=sys.argv[1] if len(sys.argv)>1 else 'names';print(json.dumps(dict(status='supported',path=r[x]) if x in r else dict(status='unsupported',request=x)));sys.exit(0 if x in r else 2)
