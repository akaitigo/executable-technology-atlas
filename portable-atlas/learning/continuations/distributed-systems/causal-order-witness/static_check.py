"""Atlas: syntax, links and exact bundle inputs; no producer/browser execution."""
import ast
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k in ('href', 'src'):
                self.links.append(v)


def main():
    checks = []
    def check(ok, label): checks.append({'passed': bool(ok), 'label': label})
    for f in ROOT.glob('*.py'):
        ast.parse(f.read_bytes(), filename=f.name)
        check(True, 'Python syntax: ' + f.name)
    for f in list(ROOT.glob('*.md')) + list(ROOT.glob('*.html')):
        if f.suffix == '.html':
            parser = Links(); parser.feed(f.read_text()); links = parser.links
        else:
            links = re.findall(r'\[[^\]]*\]\(([^)]+)\)', f.read_text())
        for link in links:
            u = urlsplit(link)
            if u.scheme or not u.path: continue
            p = (f.parent / unquote(u.path)).resolve()
            check(p.is_file() and p.is_relative_to(ROOT), f.name + ': local ' + link)
    bundle_bytes = (ROOT / 'bundle.json').read_bytes()
    bundle = json.loads(bundle_bytes)
    check(bundle['fixture_text'].encode() == (ROOT / 'inputs/events.json').read_bytes(), 'bundle fixture exact bytes')
    check(bundle['expected_text'].encode() == (ROOT / 'expected.json').read_bytes(), 'bundle expected exact bytes')
    check(hashlib.sha256(bundle_bytes).hexdigest() in (ROOT / 'lesson.js').read_text(), 'JS digest pin')
    check('description:' in (ROOT / 'SKILL.md').read_text().split('---')[1], 'Skill description in frontmatter')
    prior = json.loads((ROOT / 'records/preimplementation.json').read_text())
    for n in ['CONTRACT.md', 'expected.json', 'inputs/events.json', 'HAND_TRACE.md']:
        check(hashlib.sha256((ROOT / n).read_bytes()).hexdigest() == prior['fixed_files'][n], 'implementation-before expectations unchanged: ' + n)
    r = {'project': 'Atlas', 'passed': all(c['passed'] for c in checks), 'checks': checks,
         'check_count': len(checks), 'observation_present': bundle['run_text'] is not None,
         'producer_run': False, 'real_dom_checked': False, 'image_checked': False}
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
