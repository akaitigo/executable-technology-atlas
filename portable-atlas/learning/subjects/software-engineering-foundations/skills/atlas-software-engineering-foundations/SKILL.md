---
name: atlas-software-engineering-foundations
description: この有限教材の構成baseline、変更影響、依存closureによるtest選択を実行・説明する。実repo自動解析、工程全体や倫理評価には対応しない。
---

教材rootはこのファイルから `../..`。rootのREADME.mdとfixture.jsonを読んで、予想→操作→比較→原典/実装→答えへ案内する。

- 変更影響の実行：rootで `python3 -B runner.py --case config`。対応caseは config、price、invoice、report、audit、nochange、cycle、unknown、stale。
- 検算：`python3 -B checker.py`。通常はread-only。原票の更新を明示された場合のみ `--record` を付ける。
- 視覚比較：`python3 -B server.py` の動的loopback URLでindex.htmlを開く。専用serverを終了する。
- 未対応の実repo解析、Docker、外部API、倫理判定、製品release承認は実行せず、READMEの未教材coverageとsources.jsonのlocatorへ案内する。

configの単体PASSを製品全体PASSにしない。全path oracleと宣言graph内の一致、意図異常、baseline拒否、未実証範囲を区別する。他Subjectや旧harnessへrouteしない。
