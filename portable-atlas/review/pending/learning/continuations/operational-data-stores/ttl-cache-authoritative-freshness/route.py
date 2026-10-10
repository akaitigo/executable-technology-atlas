import json,sys
r={'ttl':'README.md','freshness':'EXPECTATIONS.md','sources':'SOURCES.md','verify':'checker.py','skill':'skills/atlas-ttl-cache/SKILL.md'}
x=sys.argv[1] if len(sys.argv)>1 else 'ttl';print(json.dumps(dict(status='supported',path=r[x]) if x in r else dict(status='unsupported',request=x)));sys.exit(0 if x in r else 2)
