---
name: atlas-backend-application-engineering
description: このmoduleのSQLite request transaction教材の実行、検査、画面、学習順へ限定して案内する。実framework、DI production、並行性能の質問は未教材と明記する。
---

# SQLite request transaction 教材への限定route

このskillは既存のmodule実装を使う。新しい技術教材・framework・broker・権限・依存関係を作らない。

1. `../../README.md`の前提→主要概念→実装→実務判断→限界→原典を読む。
2. normal routingは`python3 route.py transaction`。`../../runner.py`の既定動作はread-only検査。
3. 原票の再実行を利用者が明示した場合のみ、moduleで`python3 runner.py --record`。通常の確認で原票を書き換えない。
4. 画面はmoduleで`python3 preview.py`、出力されたloopback URLを開く。終了はCtrl-C。
5. `framework`、`production-di`、`concurrency-performance`は未対応routing。`python3 route.py framework`は`unsupported`を返し、coverage.jsonの次の実験へ案内する。現教材の成功を実frameworkやSubject全体の完成に拡張しない。
6. checker.pyのhand rowsとread-only SQLをrunnerの結果と照合する。失敗時はraw command/traceとsource digestを調べ、期待値を結果に合わせて書き換えない。
