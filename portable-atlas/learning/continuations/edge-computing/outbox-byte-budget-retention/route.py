import json,sys
import check
if sys.argv[1:]==['outbox-byte-budget-retention']:print(json.dumps(check.verify()));raise SystemExit(0)
print('unsupported topic; no writes');raise SystemExit(2)
