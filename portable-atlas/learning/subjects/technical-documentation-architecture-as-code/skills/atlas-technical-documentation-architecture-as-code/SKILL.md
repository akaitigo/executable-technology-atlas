---
name: atlas-technical-documentation-architecture-as-code
description: このAtlas教材のJSON契約、生成Markdown/SVG、stale digest、anchor、snippet stdout比較を既存runner/checker/UIで確認する。汎用文書生成や公開には使わない。
---

教材rootはこのファイルから `../..`。rootのREADME.mdの比較表と未教材coverageを読む。
正常/境界は `python3 -B run.py --scenario baseline`、古い契約は `--scenario stale-contract`、再生成比較は `--scenario regenerated`。全8条件と独立oracle検査は `python3 -B check.py`。ブラウザー確認は `python3 -B server.py` の表示するloopback URLで予想→操作→比較→原典→答えへ進む。所有serverは終了する。
通常checkerはread-only。保存物更新は依頼のある場合に限り `generate.py --write`、原票更新は `check.py --record`。未対応関数divideは既存 `run.py --scenario unsupported-function` で拒否を確認できる。
OpenAPI/Sphinx本格build、任意コード実行、公開/Site、全Subject完成を要求されたらこの教材の能力とは区別し、READMEの次の実験を案内する。新しいrunner/生成器や外部設定を作らず、対象scopeを広げない。
