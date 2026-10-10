"""Local structural routing smoke only; not an independent model evaluation."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent

def main():
    skill=ROOT/'skills/atlas-edge-computing/SKILL.md'; text=skill.read_text()
    assert text.startswith('---\nname: atlas-edge-computing\ndescription: ')
    for link in re.findall(r'\]\(([^)]+)\)',text):
        path=(skill.parent/link).resolve()
        assert path.is_relative_to(ROOT) and path.is_file(),link
    normal=['offline-logical','offline-wallclock','buffer-one','central-connected','checker.py','runner.py --record']
    unsupported=['実edge端末へdeploy','実network latencyを測定','production offline耐久性を保証']
    assert all(route in text for route in normal+unsupported) and '未対応と答え' in text
    assert '通常閲覧では原票更新しない' in text
    print('PASS: 6 normal routes / 3 unsupported routes / module-local links / read-only default; structural only')
if __name__=='__main__': main()
