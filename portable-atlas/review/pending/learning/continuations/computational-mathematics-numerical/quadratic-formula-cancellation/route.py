import sys
sys.dont_write_bytecode=True
import json
from pathlib import Path
from verify import check,sha
R=Path(__file__).resolve().parent
rows=check()['rows'];b=json.loads((R/'observations/browser.json').read_text())
assert b['observed_all_20'] and len(b['rows'])==20
for v in b['rows']:
    row=next(r for r in rows if r['fixture']==v['fixture'] and r['method']==v['method'])
    assert row['roots']==v['roots'] and [q['total_rel'] for q in row['metrics']]==v['total_rel']
assert b['peer_severe_literal_exact'] and b['scaled_residual_display_checked']
assert b['near_double_checked'] and b['rounded_double_three_layers_checked']
assert b['predictions']==['yes_correct','no_wrong','unanswered']
assert b['stale_cleared'] and b['reset_exact'] and b['source_links_clicked']==12
assert b['transport_failure_cleared_result']
http=json.loads((R/'observations/http.json').read_text())
assert len(http['normal'])==20 and all(v['status']==200 and v['exact'] for v in http['normal'])
assert len(http['refusals'])==13 and all(v['status']==400 for v in http['refusals'])
receipt=json.loads((R/'observations/receipt.json').read_text())
for name,digest in receipt['hashes'].items():assert sha(R/name)==digest
print(json.dumps(dict(browser_rows=20,http_rows=20,http_refusals=13,status='passed',scope='finite module only')))
