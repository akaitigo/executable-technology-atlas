---
name: test-order-isolation
description: 共有stateによる2テストの順序依存を実unittest processで再現し、fixture隔離と全attempt原票を比較する。
---

README、COVERAGE、hand-oracleを読む。モジュール内で`python3 -B verify.py`と`python3 -B route.py`を実行する。実childが走りPID/UTCは変わるが、原票を上書きしない。record/sealは再実行しない。

serve.pyの自身のloopback URLでoverride→defaultの共有版を操作し、defaultの8≠10とexit1を見る。逆順・fixture両順序を比較。setUp/body/assertion/tearDownのstateと、同じassertionが維持されたことを読む。成功した再実行だけを集計しない。

2テスト/2順序の決定的な共有state例であり、OS並列・全flaky原因・確率・実CI保証ではない。pytestは概念参照だけ。私的設定や既存serverを触らず、自身のserver/tabだけ終了する。旧教材はread-only。
