import json,sys
import check
if len(sys.argv)==2 and sys.argv[1]=='pulse-window-symbol-timing':print(json.dumps(check.verify()));raise SystemExit(0)
print('unsupported topic; no execution or writes');raise SystemExit(2)
