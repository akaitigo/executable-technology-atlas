"""Atlas: package exact saved bytes; absent run stays null, never synthesize a result."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--run', type=Path)
    args = p.parse_args()
    run_text = args.run.read_text() if args.run else None
    if run_text is not None:
        run = json.loads(run_text)
        if run.get('collection_complete') is not True or run.get('errors') or run.get('target_count') != 1:
            raise ValueError('only a complete successful saved observation may be displayed')
        from verify import inspect
        if not inspect(run)['passed']:
            raise ValueError('saved observation does not match fixed expectations and inputs')
    bundle = {'project': 'Atlas', 'run_text': run_text,
              'expected_text': (ROOT / 'expected.json').read_text(),
              'fixture_text': (ROOT / 'inputs/events.json').read_text(),
              'run_path': str(args.run.relative_to(ROOT)) if args.run else None}
    bundle['hashes'] = {key: hashlib.sha256(bundle[key + '_text'].encode()).hexdigest() if bundle[key + '_text'] is not None else None
                        for key in ['run', 'expected', 'fixture']}
    content = json.dumps(bundle, ensure_ascii=False, indent=2) + '\n'
    (ROOT / 'bundle.json').write_text(content)
    pin = hashlib.sha256(content.encode()).hexdigest()
    script = (ROOT / 'lesson.js').read_text()
    script, count = re.subn(r"const BUNDLE_SHA = '[^']+';", f"const BUNDLE_SHA = '{pin}';", script)
    if count != 1:
        raise ValueError('exactly one bundle pin required')
    (ROOT / 'lesson.js').write_text(script)
    print(json.dumps({'project': 'Atlas', 'bundle_sha256': pin, 'observation_present': run_text is not None}))


if __name__ == '__main__':
    main()
