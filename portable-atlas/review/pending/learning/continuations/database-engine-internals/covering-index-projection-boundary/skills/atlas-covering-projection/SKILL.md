---
name: atlas-covering-projection
description: このSQLite有限教材で、投影列とcovering index採用の境界を全結果・schema・実EQPから比較する。実性能やWAL検証には使わない。
---

基点はこのSkillの2階層上。EXPECTATIONS.md/hand-table.json/rows.jsonを読んで予想する。python3 -B runner.py / route.py / checker.pyは通常read-onlyで専用:memory:DBだけを毎回作成・closeする。UIは所有server/tabで検査する。

SELECTの列数・NULL・重複・ORDER BY label,idを全結果で照合する。index存在、schema_cover_possible、採用plan_class、比較成立を分ける。indexがあるだけでpayloadもcoveringと判断しない。EQP textはruntime依存、未認識/別planを隠さずCOMPARISON_NOT_ESTABLISHEDとして説明する。実時間や訪問page数へ換算しない。

oracle.pyはproducer/SQLを呼ばずfilter/sort/projectionする。sqlite_audit.pyは同じ実環境でschema/版/plan/結果を別照合する。通常チェックで原票を更新しない。明示--recordの旧世代を保持し、失敗statusとcleanupを報告する。

SOURCES.mdの公式locatorへ戻る。任意SQL/pathを足さず、WAL/snapshot/upgrade/他候補/global/indexを変更しない。backend README N4対応や全DB完成と称しない。公開/設定/権限変更をscopeに加えない。
