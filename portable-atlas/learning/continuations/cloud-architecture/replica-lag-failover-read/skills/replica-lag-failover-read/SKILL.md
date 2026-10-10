---
name: replica-lag-failover-read
description: この有限2store教材でA ackとB配送、read availabilityとrevision freshness、拒否と実行失敗を分けて保存原票を検査する限定Skill。
---

# replica lagとfailover read

このmodule内だけで使う。cloud製品・quorum・consensus・durability・RTOを保証しない。

1. READMEとoracle.jsonで操作順・freshness観測起点・独自ack/delivery契約を確認。
2. python3 -B route.py inspect で保存rawを独立literal表へ照合。
3. python3 -B route.py lesson のUIで正常・partition・拒否・実行失敗を予想して比較。
4. A ackをB反映やdurabilityの証明にせず、availableとfreshを分ける。
5. 明示再実行依頼がある場合のみ python3 -B route.py record。通常checkは原票を更新しない。

module外・Portal・global Skillを変更しない。観測がなければ正常答えを作らない。
