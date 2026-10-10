---
name: multiwindow-burn-alert
description: 合成eventのshort/long burnとANDの保存観測を読む・照合する・明示時だけ新規記録する。
---

このmodule内の既存worker/runner/checker/UIへrouteする。
python3 route.py inspect はread-only、lessonはUI位置を表示。
利用者が新規観測を明示したときだけ python3 route.py record。UTC別runへ追記し旧rawを保つ。
未知routeはexit2。元Subject、他continuation、Portal、利用serverへ書込・停止しない。
toy SLO90%と独自窓/閾値であり、本番pagerを提案しない。
条件変更時の予測・結果・答えresetと、入力拒否をfalseにせず予測対照できることを確認する。
