---
name: wal-snapshot-checkpoint
description: 保存済みWAL snapshot/checkpoint観測を読む、照合する、明示指定で専用DBに再記録する。
---

このmodule内だけを対象にする。`python3 route.py inspect` は保存済み証拠のread-only照合。
`python3 route.py lesson` はUIとCURRENTの位置を表示する。
利用者が新規観測を明示指定した場合だけ `python3 route.py record` を使う。
既存observationsを上書きしない。Docker、外部DB、既存サーバー、元Subjectの変更は対象外。
`runner.py`、`checker.py`、`index.html`以外の新規runner/UIを作らない。
