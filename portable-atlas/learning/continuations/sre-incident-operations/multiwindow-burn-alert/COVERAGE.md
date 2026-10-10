# 増分と未網羅

増分：元SLI/error-budget教材からshort/longの重なり、Fraction burn、>=閾値、AND／短窓だけの誤比較、集合境界89/90/99/100、分母0／未知型／重複入力拒否へ進んだ。11有限条件だけの検証。

未網羅：production SLI measurement、遅着/欠測補正、traffic重み、実clock、実alert rule、multi-level threshold/reset/suppression、実pager、on-call、incident response、緩和／復旧、postmortem、stream framework、分散収集。

次の有限実験（未実施）：

1. 低trafficの1失敗と高trafficを、分母と利用者影響を別にして比較。[Alerting on SLOs: Low-Traffic Services and Error Budget Alerting](https://sre.google/workbook/alerting-on-slos/)
2. missing/late synthetic eventsを追加し、補正前と入力確定後の分母・失敗集合を比較。[Implementing SLOs: SLI specification/implementation](https://sre.google/workbook/implementing-slos/)
3. 窓と閾値を別fixtureで変え、alert開始／resetの合成tickを手計算。実pager推奨ではない。[Multiwindow §6 / Figure5-6](https://sre.google/workbook/alerting-on-slos/)

元README・Portal・Core/fullGateは変更／実行しない。この追加で全Subject完成を主張しない。
