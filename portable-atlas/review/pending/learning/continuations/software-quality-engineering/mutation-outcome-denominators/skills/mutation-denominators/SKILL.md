---
name: mutation-denominators
description: 合成mutation reportの状態と分母を読み、未実行・無効のSurvived混入を手表と比較する。
---

README、COVERAGE、hand-oracleを読む。モジュール内で`python3 -B verify.py`と`python3 -B route.py`を再現する。record/sealで原票を上書きしない。

必要ならserve.pyの自身のloopback URLを開く。8状態各1件を一度集計し、detected2/valid4、covered3、total8を比べる。故障checkboxでvalid8へ変わる理由を元statusへ戻って読む。Pendingのみ、invalidのみ、空reportの未定義分母も確認する。

実行したのは合成report集計で、Stryker runner・自動mutation・実timeoutではない。0分母nullは教材契約。scoreを製品品質へ広げず、全科目/Coreの完成を主張しない。予想/入力変更、明示reset、拒否、旧応答無効化で古い答えを保持しない。参照元はread-only。自身のserver/tabだけを終了する。
