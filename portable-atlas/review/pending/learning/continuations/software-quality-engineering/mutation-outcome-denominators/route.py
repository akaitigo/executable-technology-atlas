import sys
sys.dont_write_bytecode=True
from verify import main
main()
from http_repair import main as repair_main
repair_main()
import json
from pathlib import Path
p=Path(__file__).resolve().parent/'observations/repair-20261008/browser.json'
u=json.loads(p.read_text())
assert u['actual_UI_transition'] and u['normal_score']=='1/2'
assert u['UI_refusal']==dict(status='REFUSED_INPUT',canonical=None,reported=None,classifications=[],answer='',summary='',diagram='',comparison='REFUSED_INPUT',open=False)
assert u['cleanup']['tab_closed'] and u['cleanup']['server_exit_status']==0 and u['cleanup']['own_port_lsof_exit_status']==1 and u['cleanup']['protected_no_actions']
assert u['direct_navigation']['not_bypassed'] and not u['direct_HTTP_browser_observations']
print('PASS: limited repair UI refusal and owned-resource cleanup')
