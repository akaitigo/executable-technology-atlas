import sys,json
routes={'interpolation':'README.md','compare':'EXPECTATIONS.md','verify':'checker.py','sources':'SOURCES.md'}
x=sys.argv[1] if len(sys.argv)>1 else 'interpolation'
print(json.dumps({'status':'supported','path':routes[x]} if x in routes else {'status':'unsupported','route':x},ensure_ascii=False))
