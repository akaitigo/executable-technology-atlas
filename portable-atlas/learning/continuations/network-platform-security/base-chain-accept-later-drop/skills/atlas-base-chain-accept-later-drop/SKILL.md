---
name: atlas-base-chain-accept-later-drop
description: 同じhookのbase chainでaccept後に別chainがdropする有限模型を実計算する。実firewall設定や安全性判定、conntrack/NAT/fragmentには使わない。
---
元Network Platform Security READMEの未教材項目から本README/事前literal fulltrace oracle/Netfilter公式manpageへ進む。priority 0/10の固定source/serviceをsortし、acceptは次base chain、dropは全体終了。故障は最初のacceptで全体終了とする一点だけ。
trusted tcp22/8080、unknown、UDP対照、service無効、JSON逆順を比較する。重複priority/未知verdict/非有限/bool/invalid packetの拒否は独立subsetであり、nft全仕様ではない。
編集JSONを実Python subprocessで評価する。実packet/final/traceから答えを生成し、全例/予想/input変更で本文とtraceを空にしてdetailsを閉じ、新値を保持する。subset/通信/実行失敗は正常答えなし。revisionで古い応答を捨てる。
通常checker/runner/QAは全unitのSHA256/mtime不変。明示recordはfresh不変原票、旧raw保存、source結合、owned server/tab cleanup。実kernel/firewall/packet/インストール/公開/Portal/他unitへ広げない。
