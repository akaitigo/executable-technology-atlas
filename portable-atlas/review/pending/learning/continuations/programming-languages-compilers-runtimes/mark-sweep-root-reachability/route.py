import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from verify import check,sha
R=Path(__file__).resolve().parent
rows=check()['rows'];b=json.loads((R/'observations/browser.json').read_text())
assert b['observed_all_18'] and len(b['rows'])==18
for v in b['rows']:
    row=next(r for r in rows if r['fixture']==v['fixture'] and r['mode']==v['mode'])
    for field in ('marked','survivors','reclaimed','premature_reclaimed','remaining_edges','steps'):assert row[field]==v[field]
assert b['rooted_all_14_steps_SVG_checked'] and b['hand_queue_black_exact']
assert b['peer_rooted_literal_exact'] and b['movement_literal_exact'] and b['masked_fault_checked']
assert b['predictions']==['no_correct','no_wrong','yes_correct','unanswered']
assert b['stale_cleared'] and b['reset_exact'] and b['source_links_clicked']==12
assert b['transport_failure_cleared_result']
http=json.loads((R/'observations/http.json').read_text())
assert len(http['normal'])==18 and all(v['status']==200 and v['exact'] for v in http['normal'])
assert len(http['refusals'])==13 and all(v['status']==400 for v in http['refusals'])
receipt=json.loads((R/'observations/receipt.json').read_text())
for name,digest in receipt['hashes'].items():assert sha(R/name)==digest
print(json.dumps(dict(browser_rows=18,http_rows=18,http_refusals=13,status='passed',scope='finite module only')))
