---
name: atlas-software-architecture
description: このmoduleのstdlib hexagonal portとin-memory/SQLite adapterの有限教材を、既存runner、checker、UI、学習順へ案内する。architecture全quality attributeの実証は未対応。
---

# 有限hexagonal教材への限定route

既存のmoduleだけを使う。新framework、外部サービス、権限、巨大台帳、別Subjectを作らない。

1. `../../README.md`の前提→主要概念→正常異常→実務判断→限界→原典を読む。
2. `python3 route.py ports-adapters`は対応route。moduleの`python3 runner.py`または`python3 checker.py`はread-only確認。
3. 利用者が再実行を明示したときだけ`python3 runner.py --record`で原票を新規保存する。確認だけで原票を更新しない。
4. UIは`python3 preview.py`のdynamic loopback URL。比較操作は保存済み原票を開く。終了はCtrl-C。
5. `production-di`、`all-quality-attributes`、`distributed-architecture`など未教材の要求は`python3 route.py all-quality-attributes`でunsupportedを返し、coverage.jsonの次の実験へ案内する。
6. 固定期待行/直接SQLとAST importの依存図を確認する。adapter同士の一致と契約への適合を区別する。固定例の成功をarchitecture全体の実証に広げない。
