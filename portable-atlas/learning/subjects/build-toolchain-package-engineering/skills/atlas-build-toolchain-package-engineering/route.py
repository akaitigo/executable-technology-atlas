import json,sys
if sys.argv[1:]==['tiny-build']:
    print(json.dumps({'supported':True,'read_only':'python3 checker.py','runner':'python3 runner.py','ui':'index.html','regeneration':'python3 runner.py --record (explicit only)'}));raise SystemExit(0)
print(json.dumps({'supported':False,'reason':'unsupported route'}));raise SystemExit(2)
