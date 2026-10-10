import json,sys
import check
if sys.argv[1:]==['anchor-and-translation-revision']:print(json.dumps(check.verify()));raise SystemExit(0)
print('unsupported topic; no writes');raise SystemExit(2)
