---
name: atlas-software-maintenance-migration
description: このmoduleの実SQLite v1→v2 staged migrationと逆移行の有限教材を、既存runner/checker/UIへ限定して案内する。本番zero downtime、他DB、一般migration toolの実証は未対応。
---

# 有限SQLite migrationへの限定route

既存moduleの実装と証拠を使う。新しいDB/外部サービス/権限/依存関係/巨大台帳を作らない。

1. `../../README.md`の前提→主要概念→正常異常→実務判断→限界→原典を読む。
2. `python3 route.py staged-migration`は対応route。moduleで`python3 runner.py`または`python3 checker.py`を実行する。既定はread-only原票検査。
3. 原票再実行が明示された場合だけ`python3 runner.py --record`で新規原票を作る。確認だけで書き換えない。
4. UIは`python3 preview.py`のdynamic loopback URL。比較操作は保存済みの実行を開く。終了はCtrl-C。
5. `production-zero-downtime`や`other-database`はunsupported routeとし、`../../coverage.json`の次の実験へ案内。transaction rollbackとcommit後の逆移行を混同せず、原値が失われた逆移行を成功と呼ばない。
6. 独立hand mapping、直接SQL、pre/post row/schema hash、raw migration traceを照合する。結果に合わせて期待値を書き換えない。
