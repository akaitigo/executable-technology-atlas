# 一次資料locatorと模型境界

2026-10-06 JST公式Web確認。本文転載なし。

- [Google SRE Workbook Implementing SLOs](https://sre.google/workbook/implementing-slos/) What to Measure: Using SLIs、SLI specification / implementation。good/totalと測定地点によるcoverage差。本例は独立台帳の既知Nとseen分母を別表示する。
- [Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) §4 Alert on Burn Rate、§6 Multiwindow。error ratioと許容error ratioの比の入口。本例のtarget4/5・tick cutoff・未知極値は独自教育値でpagerや本番目標推奨ではない。

[既存collector教材](../../observability-engineering/collector-missing-late-quantiles/README.md)は単なる未観測/確定欠落でもrequest品質は未知としている。今回もUNKNOWNを埋めず、実台帳完全性・配送・人の承認・本番判断は未確認。target100%は数学的分母0の対照で原典の目標推奨へ変換しない。
