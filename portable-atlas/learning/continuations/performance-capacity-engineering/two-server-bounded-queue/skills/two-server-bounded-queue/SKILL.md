---
name: two-server-bounded-queue
description: この有限2server教材の保存原票・FIFO状態・producer待ちとqueue待ち・cohort分母を検査する限定Skill。
---

# 有限2serverと待機容量

このmodule内だけで使う。実serverperformance/TCP/productioncapacity保証や外部変更に拡張しない。

1. READMEとoracle.jsonでoffered0・service2・FIFO・同時刻順序を確認。
2. python3 -B route.py inspect で保存rawと独立unit-tick oracleを照合。
3. python3 -B route.py lesson のUIで条件と予想を変えdrop/backpressure/入力拒否を比較。
4. producer待ち・queue待ち・service、offered/acceptedの分母を分けて説明。
5. 明示再実行依頼がある場合だけ python3 -B route.py record。通常checkは原票を更新しない。

module外の教材・Portal・global Skillは変更しない。
