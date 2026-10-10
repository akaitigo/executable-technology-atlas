# SRE：同じ50%でも、分母は同じか

synthetic request eventsを使うSLI/SLO・error budgetの有限計算教材です。固定toy SLO90%で、現実運用への目標提案や実incident対応成功は未主張。SRE／incident operations全体は未完成です。

## 学習の道筋

1. **前提**：割合、分子／分母、JSON。SLIは観測されたgood/eligible request比率、SLOは比較する目標、error budgetは許容失敗量として読み始めます。
2. **主要概念／仕組み**：窓は[0,10)、[10,20)、budget期間は[0,20)、入力確定watermarkは20。successはgood、server_errorはbad、expected_rejectionは架空契約で期待された拒否なのでeligible populationから除外。除外は普遍的ルールではなく今回のtoy定義です。時刻20は期間外、arrived>20は遅着としてdataset全体を拒否。時刻は実clockではなくsynthetic tickです。
3. **予想→操作→比較**：[UI](index.html)で予想を記入しunequal-volumeを実行。W1は0/1、W2は9/9。正しい集計は(0+9)/(1+9)=9/10、単純平均は(0%+100%)/2=50%。expected-failuresでは2拒否を除外しeligible10件のまま。budget-breachは8/10、失敗2、許容1、残量-1、burn2。window-boundariesと拒否caseも試します。
4. **原典／実装→答え**：[runner.py](runner.py)は整数/gcdの有理数で集計。[oracle.py](oracle.py)は独立Fraction手計算表と別の窓分割で検算。[fixture.json](fixture.json)のevent IDをraw窓bindingまで追います。答えは「率を平均する前に分母を確認し、goodとeligibleの数を合計する」。display小数は補助で分数が正本です。
5. **実務判断**：何をgood/eligibleとするか、期間境界、データの欠落・遅着を先に確認。分母が0なら100%にも0%にもせず、評価対象なしとして拒否。部分窓を黙って省かない。budget残量の負値は超過量で、0にclampしません。toy計算からrelease停止・pager閾値を勝手に決めません。
6. **限界**：固定SLO、2つの完全な非重複窓、最大100events、架空分類、stream処理や実monitoringなし。watermark後の再計算、重複排除、収集欠落補正、分散clock、latency SLI、multiwindow alert、実on-call、communication、緩和、復旧、postmortemは未実証。期間途中のrequest数から求める許容数は数学上の比例量で整数への切上げはしません。
7. **原典**：[sources.json](sources.json)からGoogle SREとFraction仕様へ。教材のbudget計算は原典概念の小さな適用例。目標と除外基準は利用者体験と合意に基づく別の判断です。

## 再現

このディレクトリでPython3.9以降、標準ライブラリのみ。

```sh
python3 -B runner.py --case unequal-volume
python3 -B checker.py
python3 -B checker.py --record
python3 -B server.py
```

通常checkerはread-only、原票更新は明示`--record`だけ。serverの動的127.0.0.1 URLを開き、Ctrl-Cで終了。UIは実runnerの分数と窓eventを描画し、業務計算をJavaScriptで複製しません。

[実行原票](observations/run.json)に実行UTC時刻・環境・input/raw・source/artifact digest。[実IAB QA](observations/qa.json)、[session/cleanup](observations/session.json)、[限定Skill](skills/atlas-sre-incident-operations/SKILL.md)も保存します。

## 未教材coverageと次の問い

| 主要範囲 | 今回判断できること／残る問い | 次の実験（未実施） | 一次資料locator |
| --- | --- | --- | --- |
| SLI/SLO定義とmeasurement | 分母・good・除外を説明できる。ユーザー体験の何を測り、欠測をどう扱う？ | 架空サービスでavailabilityとlatencyのSLI、client/server観測差、遅着再計算を比較 | [Implementing SLOs](https://sre.google/workbook/implementing-slos/) SLI specification / implementation |
| burn alert・budget policy | toy burnと残量を計算できる。複数窓でpagerに値する持続影響をどう見分ける？ | fixed100eventsのshort/long burnと単発errorを比較し、仮policyのdecisionを記録 | [Alerting on SLOs](https://sre.google/workbook/alerting-on-slos/) Multiwindow / Multi-Burn-Rate、[Budget Policy](https://sre.google/workbook/error-budget-policy/) |
| incident response・on-call・緩和／復旧 | 数値は対応判断の材料。指揮・連絡・緩和・復旧確認を誰がどう行う？ | 架空tabletopで役割、timestamped status、rollbackと復旧確認を比較。通信欠落も反例に | [Managing Incidents](https://sre.google/sre-book/managing-incidents/) Elements of Incident Management |
| postmortem・toil・継続改善 | 観測と推測を分けられる。原因候補と再発防止をどう検証する？ | 同じ架空incidentをblamelessに記録し、改善actionの再試験とtoil時間を比較 | [Postmortem](https://sre.google/sre-book/postmortem-culture/)、[Eliminating Toil](https://sre.google/sre-book/eliminating-toil/) |

まず正確な分母と期間を確認し、測定設計、alert/policy、response、事後改善へ進んでください。この4実験は計画であり実施証拠ではありません。
