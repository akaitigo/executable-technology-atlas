---
name: atlas-api-integration-contracts
description: 保存済みstdlib loopback HTTP教材でJSON契約の互換・破壊的変更、status/media/error/timeoutの判定を説明・検査する。外部APIや認証/TLS操作には使わない。
---

# HTTP JSON契約教材

2階層上がmodule root。[README](../../README.md)の固定契約と[COVERAGE](../../COVERAGE.md)を読む。

- 正常/変更/timeoutの質問は`evidence/stdout.json`の対応caseへroute。通信受信・item受入・処理済み業務エラー・拒否を区別し、200だけでschema合格にしない。timeoutからserver未処理や再送安全性を推定しない。
- 根拠は[契約](../../contract.json)、[client](../../client.py)、[実runner](../../experiment.py)、[独立case Oracle](../../verify.py)、[公式locator](../../sources.json)へ結ぶ。`index.html`は保存原票再生。
- 検査はmodule rootで`python3 -B verify.py`または`python3 -B observe.py`。通常はread-onlyでserverを起動しない。原票更新が依頼された時だけ`python3 -B observe.py --write-evidence`でowned dynamic loopback実行。外部接続へ変更しない。
- 実API、auth/TLS、retryの安全性、全JSON Schema/OpenAPI、性能/SLOは未実施を明示し、READMEの次の実験へ案内。自動で外部操作や新契約を追加しない。

時刻・環境・source/Artifactは`evidence/run.json`/`artifacts.json`、画面QA/capture保存有無は[QA](../../QA.md)。静的Skill検証だけで全Subject完成や独立Agent評価を主張しない。
