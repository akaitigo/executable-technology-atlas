---
name: atlas-reservation-invariant
description: この有限2 replica教材で、予約応答・収束・在庫上限を実行証拠から比較する。実予約やCAP証明には使わない。
---

基点はこのSkillの2階層上。EXPECTATIONS.md、hand-trace.json、fixture.jsonを読んで予想する。通常のrunner.py/route.py/checker.pyをpython3 -Bで実行する。UIの操作と原票を照合する場合は自身のserver/tabを用いる。

acceptedの業務上限は全response_historyでacceptedを返した異なるID数から読む。local集合やconvergedだけで安全を判定しない。pendingは未決定であり、accepted/rejectedに丸めない。復旧・直列判定・snapshot配送を別eventとして説明する。重複はdelivered_setとdelivery_countを比べる。応答履歴は同期でも保持する。

oracle.pyはmodelの配送関数を呼ばない。全trace、独立集合式、手書きliteralを照合し、不一致は証拠を保持して報告する。通常CLIはread-only。原票の更新は明示された--recordのみで、古い原票を削除しない。原典はSOURCES.mdのp.559。予約規則は独自である。global/index/既存候補を更新せず、実通信・CRDT・CAP・合意・取消補償まで推論を広げない。
