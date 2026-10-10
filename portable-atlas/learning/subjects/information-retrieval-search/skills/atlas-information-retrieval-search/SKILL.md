---
name: atlas-information-retrieval-search
description: 保存済みPython Boolean転置index教材でAND/OR、stale・missing hit、rebuild回復を説明・検査する。製品engineやranking/semantic検索の操作には使わない。
---

# Boolean検索教材

このSkillの2階層上が教材root。[README](../../README.md)と[COVERAGE](../../COVERAGE.md)で範囲を確認する。

- AND/OR、token境界、更新後の不一致には`evidence/stdout.json`と`evidence/verification.json`を読む。`index.html`は実原票の再生。postingと現在documentを区別し、stale hitとmissing hitを成功へ書き換えない。
- 検査は教材rootで`python3 -B verify.py`または`python3 -B observe.py`。通常はread-only。原票更新が依頼された時だけ`python3 -B observe.py --write-evidence`で実runnerを実行する。
- 根拠は[原典locator](../../sources.json)、[indexer](../../indexer.py)、独立full scanの[checker](../../verify.py)へ結ぶ。実行時刻・版は`evidence/run.json`から読む。
- BM25、速度倍率、semantic embedding、製品engine、日本語解析などには「この教材では未確認/未教材」と答える。追加実装や外部サービスへ自動で広げず、保存結果から順位・性能を推定しない。

画面QAと保存captureの有無は[QA](../../QA.md)へ。Subject全体の完了や独立Agent評価の実施を、このSkillの静的検証だけで主張しない。
