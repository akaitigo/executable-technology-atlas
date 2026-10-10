"""Atlas: saved text fixtures only; no OS process reads or target execution."""
import json
from resource_parse import parse_processes

cases = [
    ('valid-no-match', '123 1 0.0 4000 /usr/bin/python3\n124 1 0.0 4000 /usr/bin/java\n', 0, True, 0),
    ('valid-heavy', '123 1 0.0 4000 /usr/bin/python3\n124 1 30.0 4000 /usr/bin/rustc\n', 0, True, 1),
    ('empty', '', 0, False, None),
    ('all-invalid', 'invalid\n', 0, False, None),
    ('mixed-invalid', '123 1 0.0 4000 /usr/bin/python3\ninvalid\n', 0, False, None),
    ('self-missing', '124 1 0.0 4000 /usr/bin/java\n', 0, False, None),
    ('failed-read', '123 1 0.0 4000 /usr/bin/python3\n', 1, False, None),
]
results = []
for name, data, exit_code, trusted, count in cases:
    observed = parse_processes(data, exit_code, 123)
    assert observed['trusted'] == trusted
    assert (len(observed['heavy']) if observed['heavy'] is not None else None) == count
    results.append({'case': name, 'input': {'stdout': data, 'exit_code': exit_code, 'own_pid': 123}, 'passed': True, 'observed': observed})
print(json.dumps({'project': 'Atlas', 'simulated_only': True, 'new_native': 0, 'cases': results}, indent=2))
