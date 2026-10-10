# 同じ2件正解でも、確率の二乗誤差は違う

[元AI教材](../../../subjects/ai-evaluation-safety/README.md) Coverageの「score較正未証明・calibration未教材」から、二値確率のBrier lossだけを進める有限教材です。作者が置いた整数percentであり、学習済みモデルや現実属性ではありません。

## 予想 → 実処理 → 比較 → 答え

前提は二値label、threshold、分数、平均。元混同行列→このprobability loss→reliability diagram/held-out/confidence interval（未制作）の順で読みます。thresholdはpercent ≥50、正例の確率はFraction(percent,100)。二値Brierは平均 (p−label)²、範囲0..1。多クラスの全class和0..2定義とは区別します。

| labels=[1,0] のpercent | 各sample寄与 | 二値正解数 | 確率Brier |
|---|---|---|---|
| [60,40] | 4/25, 4/25 | 2/2 | 4/25 |
| [90,10] | 1/100, 1/100 | 2/2 | 1/100 |
| [90,90] | 1/100, 81/100 | 1/2 | 41/100 |
| [100,0] | 0, 0 | 2/2 | 0 |
| [0,100] | 1, 1 | 0/2 | 1 |
| [73,40] | 729/10000, 4/25 | 2/2 | 2329/20000 |
| [50,50] | 1/4, 1/4 | 1/2 | 1/4 |

故障版はclass 0/1をscoreとして計算し、最初の2入力をどちらもloss0と誤報します。独立oracleは実際のpercentの寄与/平均を出し、この取り違えを表示します。perfect入力ではclass流用でも同じ0になるので、単一の成功例で故障版を正しいとしません。

~~~sh
python3 -B runner.py --record
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py inspect
python3 -B route.py lesson
python3 -B preview.py
~~~

previewの127.0.0.1動的URLを開き、正解数と約分済みBrier分数を予想→「実処理して比較」→raw/model/oracle→答え。JSON percentの一箇所を編集して実行し直すと、各ID寄与/平均/答えが新入力へ追従します。固定2件以外も1..8件を同じ実経路で受け付けます。条件変更は予想も空へ。予想・入力変更は新値を保持し、旧結果/答え/rawを空にしてdetailsを閉じます。旧非同期応答はgenerationで破棄し、新入力を上書きしません。

## 実装 → 独立検証 → 原票

[事前literal表](oracle.json)をproducerより先に作成。[model](model.py)はFraction、[checker](checker.py)はproducerをimportせず整数差の平方/10000とgcdで約分する別経路。固定表の各sample/平均/正解数とも照合します。UIはJSでscoreを代算せず、[実行入口](execute.py)が毎回model実子processと独立audit実子processを起動。input/UTC/argv/exit/stdout/stderr/sourceHashesをrawで保持します。audit failureは結果へ進めません。

recordだけが新UTC directoryとCURRENTを作ります。旧rawは上書きしません。default runner/checker/inspect/lessonはread-only。UI処理はメモリ上のreceiptだけで保存原票へ書き込みません。30000byte以下の入力に限定し、外部pathやサービスへ接続しません。qaDelay=2000は旧応答破棄QAのためHTTP応答だけを2秒保留し、model/audit実行時刻は実子processの直前直後です。

空入力列、重複ID、bool、非有限値、整数範囲外、label型、非整数percent、schemaはREFUSED/exit2。JSON破損は実decode失敗/exit3/stdout空。これらのscoreは未観測で0とは違います。独立audit/HTTPの失敗、旧応答破棄も正常scoreに混ぜません。[QA](QA.json)でreadonly SHA/mtime、実IAB、可変入力、stale、capture、資源終了を記録します。

## 一次資料と限界

[scikit-learn公式Brier定義](https://scikit-learn.org/stable/modules/model_evaluation.html#brier-score-loss)のbinary mean squared errorを実装へ接続。[公式較正解説](https://scikit-learn.org/stable/modules/calibration.html)はlossがreliabilityだけでなくresolution等も含み、低Brierが較正改善だけを意味しない点へ接続します。stdlib実行のみでsklearnはinstall/importしていません。

固定2～数件のloss差は、scoreの較正、母集団の代表性、未知データのモデル品質、safety認定を証明しません。reliability/held-out/CI、学習・leakage、shift、fairness、現実モデル、安全性評価は[残範囲](COVERAGE.md)。元unit/Portal/Core/fullGate/shared DB/settings/install/commit/push/公開は割当外。全Subject完成を主張しません。
