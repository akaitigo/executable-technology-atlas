"""Join saved bytes for the reader. Never run or import the role model."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sha = lambda b: hashlib.sha256(b).hexdigest()


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--raw', type=Path); args = ap.parse_args()
    body = {'project': 'Atlas', 'raw_text': None, 'raw_sha256': None}
    for key, name in [('fixture', 'inputs/cases.json'), ('expected', 'expected.json')]:
        data = (ROOT / name).read_bytes(); body[key + '_text'] = data.decode(); body[key + '_sha256'] = sha(data)
    if args.raw:
        from verify import inspect
        data = args.raw.read_bytes()
        if not all(c['passed'] for c in inspect(json.loads(data))):
            raise SystemExit('Only verified completed saved results can be connected')
        body.update(raw_text=data.decode(), raw_sha256=sha(data))
    data = (json.dumps(body, ensure_ascii=False, indent=2) + '\n').encode()
    (ROOT / 'bundle.json').write_bytes(data)
    p = ROOT / 'lesson.js'; script = p.read_text()
    script, count = re.subn(r"const BUNDLE_SHA='[^']*';", "const BUNDLE_SHA='" + sha(data) + "';", script)
    if count != 1:
        raise SystemExit('one bundle pin required')
    p.write_text(script)
    print(json.dumps({'project': 'Atlas', 'bundle_sha256': sha(data), 'saved_raw_present': args.raw is not None, 'target_runs': 0}))


if __name__ == '__main__':
    main()
