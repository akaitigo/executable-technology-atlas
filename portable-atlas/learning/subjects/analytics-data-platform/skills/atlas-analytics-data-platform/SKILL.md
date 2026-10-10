---
name: atlas-analytics-data-platform
description: 保存済みSQLite教材でorder/line grain、JOIN重複集計、preaggregate/EXISTS、dimension/NULL境界を説明・検査する。実DWH/lake/BI製品の操作や性能判断には使わない。
---

# order grain教材

2階層上が教材root。[README](../../README.md)の指標定義と[COVERAGE](../../COVERAGE.md)を先に読む。

- 重複集計の依頼は`evidence/stdout.json`のnaive/preaggregate/semi/distinctへroute。手集計280、SQL観測380/280/280/180、異常を正常に書き換えない。dimension/NULL/emptyは対応caseの件数とSUMを併記する。
- SQLとlineageは[queries](../../queries.json)、[runner](../../experiment.py)、[独立固定手集計Oracle](../../verify.py)へ結ぶ。`index.html`は実原票の説明用再生で、物理execution planではない。
- 通常検査は教材rootで`python3 -B verify.py`または`python3 -B observe.py`。read-only。原票更新が依頼された時だけ`python3 -B observe.py --write-evidence`。時刻・版・digestは`evidence/run.json`から読む。
- 実DWH/lake/BI、性能倍率、SCD/増分ETLなど未実施の依頼は未教材/未確認を明示し、READMEの次の実験へ案内する。外部サービス・別指標へ自動拡張しない。

[原典locator](../../sources.json)と[QA](../../QA.md)で根拠・画面確認範囲・capture保存有無を区別する。静的Skill検証だけで全Subject完成や独立Agent Evalを主張しない。
