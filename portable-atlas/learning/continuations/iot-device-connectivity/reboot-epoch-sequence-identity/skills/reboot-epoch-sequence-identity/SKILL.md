---
name: reboot-epoch-sequence-identity
description: 合成deviceのreboot epoch/seq identityとhistory/latestの有限教材を読み取り検査または明示再記録する。
---

module rootでpython3 -B route.py inspect / lessonを使う。元device HWM→本単元→key-generation CASの読む順を保つ。
通常checkerはreadonly。明示更新のみrunner.py --recordで新UTC原票、旧raw保持。epoch発行はfixture前提、MQTT規定や実rebootとして扱わない。install/settings/broker/credential操作を行わない。
