import json,sys
r={'selective':'README.md','contract':'EXPECTATIONS.md','sources':'SOURCES.md','verify':'checker.py','skill':'skills/atlas-selective-measurement/SKILL.md'}
x=sys.argv[1] if len(sys.argv)>1 else 'selective';print(json.dumps(dict(status='supported',path=r[x]) if x in r else dict(status='unsupported',request=x)));sys.exit(0 if x in r else 2)
