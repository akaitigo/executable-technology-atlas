---
name: atlas-sql-window-frames-peers
description: SQL第2単元の既存SQLite保存DB・read-only window結果からRANGE peerとROWS frame集合を比較する。
---
このcontinuation moduleの既存runner/checker/UIだけへrouteする。ルートはこのファイルの2階層上。
`python3 skills/atlas-sql-window-frames-peers/route.py window-peers` でread-only経路を表示。
通常は `python3 runner.py` 又は `python3 checker.py`。原票更新は明示的要求時だけ `python3 runner.py --record`。
UIは `index.html`、一時previewは `python3 preview.py`。確認後owned tab/serverを終了する。
未対応routeはexit2。保存fixture DBはread-only/query_onlyで照合する。元SQL subjectはread-only参照に限り、source/raw/QA/binding/Skillを更新しない。外部DB、旧PG、既存Goal、公開/commit/pushを行わない。
