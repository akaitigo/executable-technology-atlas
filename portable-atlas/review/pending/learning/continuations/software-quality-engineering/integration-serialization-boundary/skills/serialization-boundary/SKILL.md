---
name: serialization-boundary
description: 両端pure unitと実HTTPのserialization境界を比較し、JSON型・単位・HTTP状態・意味一致を分ける有限教材を再現する。
---

README、COVERAGE、hand-oracleを読む。モジュール内でverify.pyとroute.pyをpython3 -Bで再現する。実owned loopback childが必要で、sandbox拒否は失敗として扱う。既存権限の範囲でhost permission reviewを使う。保存record/sealは再実行しない。

serve.pyの自身のloopback URLで1000msの故障serializer/coerceを実行し、unit passでもHTTP200/1msで意味不一致を読む。strictの400拒否、normalの意味一致、2000msの同条件を比較する。全attemptとreceiver wireを保持し、有利なretryだけを選ばない。

JSON/HTTP標準と独自ms契約を分ける。unitはadapter未検査。E2E全般や実製品品質へ一般化しない。自身のserver/tab/Popenだけを終了し、旧教材と既存listenerへ触れない。
