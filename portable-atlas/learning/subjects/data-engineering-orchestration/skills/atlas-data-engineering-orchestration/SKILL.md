---
name: atlas-data-engineering-orchestration
description: 固定CSVのtyped変換、dedup、quarantine、再実行とpublish失敗をこの有限教材で比較する。
---
このmoduleの既存runner/checker/UIだけを使う。ルートはこのファイルの2階層上。
`python3 skills/atlas-data-engineering-orchestration/route.py csv-pipeline` は既存実行へのread-only経路を表示する。
通常確認は `python3 runner.py` または `python3 checker.py`。原本の再生成は明示的に要求された時だけ `python3 runner.py --record`。
UIは `index.html`。一時previewは `python3 preview.py`、動的loopback portを使用し終了時に停止する。
未対応routeはexit2。production scheduler・remote ETL・外部サービスを実行済みとして扱わない。他の教材やroot文書を変更しない。
