import sys,json
routes={'priority':'README.md','compare':'EXPECTATIONS.md','sources':'SOURCES.md','verify':'checker.py'}
x=sys.argv[1] if len(sys.argv)>1 else 'priority';print(json.dumps(dict(status='supported',path=routes[x]) if x in routes else dict(status='unsupported',request=x),ensure_ascii=False))
