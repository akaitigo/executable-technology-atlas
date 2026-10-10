import json,sys
r={'skill':'skills/atlas-reflow-focus/SKILL.md','reflow':'README.md','focus':'EXPECTATIONS.md','sources':'SOURCES.md','verify':'checker.py'}
x=sys.argv[1] if len(sys.argv)>1 else 'reflow';print(json.dumps(dict(status='supported',path=r[x]) if x in r else dict(status='unsupported',request=x)));sys.exit(0 if x in r else 2)
