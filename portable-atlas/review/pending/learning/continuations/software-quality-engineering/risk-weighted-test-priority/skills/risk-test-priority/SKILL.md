---
name: risk-test-priority
description: 固定impact重みと予算を使い、有限subset最適性・critical制約・実Python境界検査を分けて読む教材を再現する。
---

本教材のREADME、COVERAGE、hand-oracleを読む。モジュール内で`python3 -B verify.py`と`python3 -B route.py`を実行する。保存原票を上書きするrecord/sealを再実行しない。

必要ならserve.pyを起動し、表示された自身のloopback URLを開く。予算3でgreedy 14と最適15、critical必須の予算0/1でINFEASIBLE、upperのB未実施と検出の違いを操作する。予想変更と条件変更では旧答え・raw・表が消えることを確認する。

scoreは恣意的impactで確率・品質ではない。costは実時間ではない。NOT_RUNと差なしと検出を分ける。全16subsetの最適性を実製品や一般のrisk-based testingへ広げない。新しい有限契約は別の教材として明示し、封印済み手表と原票を修正しない。自身のserver/tabだけを終了する。
