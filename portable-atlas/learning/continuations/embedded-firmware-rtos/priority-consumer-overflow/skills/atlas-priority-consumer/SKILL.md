---
name: atlas-priority-consumer
description: この有限教材でpriority job選択・長いconsumer・有界待機queueのdrop/待ち/完了を比較する。実IRQ/RTOS/WCET/Safety保証やSMP検証には使わない。
---

rootはこのSkillの2階層上。`python3 -B route.py priority`→README、`compare`→契約と手表、`sources`→一次資料、`verify`→checkerへ進む。前のISR offload単位から、待機の受入とservice完了を分離する。priorityは受入済みjobの選択、処理中はpreemptionなし、同着input順を維持する。予想→操作→正常/overflow/priority/誤報→実trace/SVG→source/raw→実結果の答え。未知routeはunsupportedを返す。通常はread-only、新原票だけ明示record。実RTOSや無限到着・deadline・Safety保証へ拡張せず、Subject全体の完成と呼ばない。
