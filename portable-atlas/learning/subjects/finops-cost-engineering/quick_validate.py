"""Local skill structural routing smoke; no model behavior or external finance action."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent

def main():
    skill=ROOT/'skills/atlas-finops-cost-engineering/SKILL.md';text=skill.read_text()
    assert text.startswith('---\nname: atlas-finops-cost-engineering\ndescription: ')
    for link in re.findall(r'\]\(([^)]+)\)',text):
        path=(skill.parent/link).resolve();assert path.is_relative_to(ROOT) and path.is_file(),link
    normal=['equal-conserved','equal-naive','tie-reordered','missing-tag','checker.py','runner.py --record']
    unsupported=['実クラウド価格を取得','billing APIで請求変更','実税額を計算','契約購入の財務判断']
    assert all(route in text for route in normal+unsupported) and '未対応と答え' in text
    assert '通常閲覧では原票更新しない' in text
    print('PASS: 6 normal routes / 4 unsupported routes / module-local links / read-only default; structural only')
if __name__=='__main__':main()
