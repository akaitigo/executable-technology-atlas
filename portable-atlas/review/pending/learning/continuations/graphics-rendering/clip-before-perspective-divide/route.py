import json,sys
routes={'clip':'README.md','contract':'EXPECTATIONS.md','sources':'SOURCES.md','verify':'checker.py','skill':'skills/atlas-near-plane-clip/SKILL.md'}
x=sys.argv[1] if len(sys.argv)>1 else 'clip';print(json.dumps(dict(status='supported',path=routes[x]) if x in routes else dict(status='unsupported',request=x)));sys.exit(0 if x in routes else 2)
