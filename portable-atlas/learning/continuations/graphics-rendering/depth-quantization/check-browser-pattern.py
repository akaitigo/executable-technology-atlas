"""Atlas: finite process-name strings only; no ps, child, browser or model execution."""
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('gate', ROOT / 'resource-gate.py')
gate = importlib.util.module_from_spec(spec); spec.loader.exec_module(gate)
policy = {'known_idle_identities': [], 'known_idle_group_cpu_at_most': 0}
names = ['/fixture/chrome_crashpad_handler', '/fixture/Brave Browser', '/fixture/Opera',
         '/fixture/headless_shell', '/fixture/headless-shell', '/fixture/Chrome',
         '/fixture/Chromium', '/fixture/Firefox', '/fixture/Safari', '/fixture/Microsoft Edge',
         '/fixture/msedge', '/fixture/com.apple.WebKit.GPU.WebContent', '/fixture/chrome-native-host',
         '/fixture/playwright', '/fixture/java', '/fixture/geckodriver', '/fixture/flutter_tester']
checks = []
for comm in names + ['/fixture/python3']:
    row = {'pid': 1000001, 'ppid': 1, 'lstart': 'synthetic', 'comm': comm, 'cpu': 0.0}
    observed = gate.assess([row], policy, True)
    expected = comm == '/fixture/python3'
    assert observed['process_condition_passed'] is expected, comm
    checks.append({'comm': comm, 'expected_pass': expected, 'observed': observed})
report = {'title': 'Atlas current browser-name union checks', 'passed': True, 'checks': checks,
          'source_sha256': {n: hashlib.sha256((ROOT / n).read_bytes()).hexdigest()
                            for n in ['resource-gate.py', 'check-browser-pattern.py']},
          'process_observations': 0, 'target_runs': 0, 'all_browser_detection_guaranteed': False}
(ROOT / 'observations/browser-pattern-check.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': True, 'string_cases': len(checks), 'target_runs': 0}))
