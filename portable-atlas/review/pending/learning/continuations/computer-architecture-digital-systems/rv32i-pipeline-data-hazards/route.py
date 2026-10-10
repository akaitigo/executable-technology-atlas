import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from verify import check,sha
R=Path(__file__).resolve().parent
rows=check()['rows']
b=json.loads((R/'observations/browser.json').read_text())
assert len(b['rows'])==27 and b['observed_all_27']
for item in b['rows']:
    row=next(r for r in rows if r['fixture']==item['fixture'] and r['mode']==item['mode'])
    for field in ('cycles','stalls','registers'): assert row[field]==item[field]
assert b['rendered_chain_stall_hand_table_exact'] and b['priority_MEM_over_WB']
assert b['stale_cleared'] and b['reset_exact'] and b['source_links_clicked']==11
assert b['predictions']==['yes_wrong','yes_correct','no_wrong','unanswered']
assert b['transport_failure_cleared_result']
h=json.loads((R/'observations/http.json').read_text())
assert len(h['normal'])==27 and all(x['exact'] and x['status']==200 for x in h['normal'])
assert len(h['refusals'])==13 and all(x['status']==400 for x in h['refusals'])
receipt=json.loads((R/'observations/receipt.json').read_text())
for name,digest in receipt['hashes'].items():assert sha(R/name)==digest
print(json.dumps(dict(browser_rows=27,http_rows=27,http_refusals=13,scope='finite route only',status='passed')))
