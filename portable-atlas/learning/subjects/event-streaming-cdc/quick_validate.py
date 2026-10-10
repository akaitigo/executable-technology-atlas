"""Dependency-free local skill route smoke check; not a model behavioral evaluation."""
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent

def main():
    path=ROOT/'skills/atlas-event-streaming-cdc/SKILL.md'
    text=path.read_text()
    assert text.startswith('---\nname: atlas-event-streaming-cdc\ndescription: ')
    assert len(text.split('---',2))==3
    for link in re.findall(r'\]\(([^)]+)\)',text):
        assert (path.parent/link).resolve().is_relative_to(ROOT)
        assert (path.parent/link).is_file(),link
    normal={'source通知':'coupled','再読':'replay-idempotent','検算':'checker.py','更新':'runner.py --record'}
    for route in normal.values(): assert route in text,route
    unsupported=['実WAL CDCを読んで','Kafka本番へ接続','production exactly-onceを保証']
    assert all(prompt in text for prompt in unsupported) and '未対応と答え' in text
    assert '通常閲覧で原票を更新しない' in text
    print('PASS: normal routes=4; unsupported routes=3; module-local links; read-only default. Structural smoke only.')
if __name__=='__main__': main()
