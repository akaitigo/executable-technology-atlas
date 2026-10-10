"""Atlas: bind exact saved bytes; no target execution or expected-value simulation."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--run', type=Path); args = ap.parse_args()
    expected = (ROOT / 'expected.json').read_bytes(); fixture = (ROOT / 'inputs/cases.json').read_bytes()
    body = {'project': 'Atlas', 'expected_text': expected.decode(), 'expected_sha256': sha(expected),
            'fixture_text': fixture.decode(), 'fixture_sha256': sha(fixture), 'run_text': None, 'run_sha256': None}
    if args.run:
        from verify import inspect
        data = args.run.read_bytes(); run = json.loads(data)
        if not all(x['passed'] for x in inspect(run)):
            raise SystemExit('Only verified completed saved output may be connected')
        body.update(run_text=data.decode(), run_sha256=sha(data))
    data = (json.dumps(body, ensure_ascii=False, indent=2) + '\n').encode()
    (ROOT / 'bundle.json').write_bytes(data)
    script = ROOT / 'lesson.js'; text = script.read_text()
    text, count = re.subn(r"const BUNDLE_SHA='[^']*';", "const BUNDLE_SHA='" + sha(data) + "';", text)
    if count != 1:
        raise SystemExit('one explicit bundle pin is required')
    script.write_text(text)
    print(json.dumps({'project': 'Atlas', 'bundle_sha256': sha(data), 'observation_present': args.run is not None,
                      'target_executed': False, 'pending_is_not_simulated_measurement': True}, indent=2))


if __name__ == '__main__':
    main()
