# AI評価と安全性を学ぶ道筋

この文書は[固定binary評価の既存教材](README.md)から、評価データ、閾値、失敗の費用、利用状況ごとのリスクへ進むための補足です。有限教材の補足であり、分野全体の学習完了を示すものではありません。以下の次実験はすべて未実行です。

## 1. 前提と主要概念

割合の分子・分母、集合の分類、確率と標本の区別を押さえます。最初に、labelは何の正解か、陽性は何を意味するか、誰がlabelを決めたかを説明します。Pythonのlistと関数を理解すると実装を読めます。

学ぶ順序は **タスクと失敗の定義 → データと正解 → scoreとdecision → 混同行列とmetric → 評価分割と不確実性 → 集団・分布・攻撃 → 運用とリスク管理** です。

- scoreは閾値判定の入力です。0〜1の数というだけでは確率として較正されていません。
- Accuracy、Precision、Recall、FPRは違う分母を持ちます。閾値の適否は見逃しと誤警報の費用に依存します。
- 計算が正しいこと、データが代表的なこと、モデルが未知入力に汎化することは別の検査です。
- 安全性評価では、想定用途・影響を受ける人・失敗条件を先に定めます。単一の分類metricだけでprivacy、公平性、攻撃耐性や運用安全を説明できません。

## 2. 予想から既存実測へ

[UI](index.html)で閾値を上げたときのFN/FPと分母を予想し、[入力](predictions.json)、[手集計Oracle](hand-count.json)、[実装](evaluate.py)、[原票](evidence/observation.json)、[環境・digest](evidence/verification.json)を読みます。この文書作成では集計を再実行していません。

| 閾値 | 保存済み TP / FN / FP / TN | Accuracy | Precision / Recall |
|---|---|---|---|
| 0.30 | 2 / 0 / 2 / 16 | 90% | 50% / 100% |
| 0.50 | 1 / 1 / 1 / 17 | 90% | 50% / 50% |
| 0.80 | 1 / 1 / 0 / 18 | 95% | 100% / 50% |
| 0.90 | 0 / 2 / 0 / 18 | 90% | 未定義 / 0% |

20合成件のうち実陽性は2、実陰性は18です。この固定fixtureでは閾値を上げるとFPが減り、FNが増えます。同じAccuracy 90%でも検出できた陽性は2・1・0件なので、「同じAccuracyなら同じ働き」という予想は外れます。0.80と同じscoreのp01は`>=`規則で陽性に残ります。

正常系は各sampleを4分類し、分子・分母を保存することです。陽性予測0件のPrecisionは分母0のためJSON `null`と`undefined-zero-denominator`であり、エラーを隠して0%へ置換していません。不正入力として空データ、非binary label、NaN/infinity、範囲外値、重複IDなどを拒否する検査がREADMEと[QA](QA.md)に記録されています。今回はそのcheckerを動かしていません。

scoreは作者が設定した値です。学習済みモデルも外部APIも使っておらず、モデル品質・統計的信頼性・安全性の実測ではありません。UIとSVGは保存集計の説明であり、QAにあるdesktop確認をmobile・直接file表示の確認へ拡張しません。

## 3. 実務で何を判断するか

まず失敗をsample IDで追い、FN/FPの費用、評価の対象期間と母集団、labelの曖昧さを記します。閾値はvalidationデータで決め、最終testを繰り返し調整に使わない契約を作ります。全体割合に加え、分母、用途別の内訳、未知・対象外の入力も報告します。

運用判断には、代表的データと不確実性、分布の変化、失敗時の影響、監視と停止・修正の責任が必要です。分類集計のpassを根拠にモデル全般の安全を許可せず、必要な評価項目を利用状況から定めます。生成タスクでは正誤に加え、rubric、評価者の一致、拒否し過ぎ、有害な実行、根拠の欠落などを分けて記録します。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [Google Classification metrics](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall)、Accuracy / Recall / FPR / Precision / NaN | 既存の数式と分母0のbinding |
| [Google Thresholds and confusion matrix](https://developers.google.com/machine-learning/crash-course/classification/thresholding)、Classification threshold / Confusion matrix | 既存の閾値と4分類のbinding |
| [Google ROC and AUC](https://developers.google.com/machine-learning/crash-course/classification/roc-and-auc)、ROC / AUC / Precision-recall curve | 閾値を横断した比較とclass imbalanceへの注意 |
| [Google Dividing datasets](https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets)、Training, validation, and test sets / Additional problems with test sets | testの使い回し、重複、現実分布とのずれ |
| [NIST AI RMF Core 1.0](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)、§5.2 Map / §5.3 Measure / §5.4 Manage | 文脈から評価・対処へつなぐ。適合認証や固定チェックリストではない |

既存のbindingは[sources.json](sources.json)にあります。NISTの枠組みは安全なscoreを一つ計算する手順ではなく、用途に応じてリスクを扱うための原典として読みます。

## 5. 具体的な未教材coverage

| 未教材 | まだ確かめていないこと |
|---|---|
| 学習、分割、leakage、cross validation | 評価データが調整や学習へ混入していないか |
| ROC/PR/AUC、calibration、信頼区間 | 全閾値の挙動、確率との対応、少数sampleの不確実性 |
| multi-class、ranking、生成・LLM評価 | binary以外の正解、rubric、評価者の信頼性 |
| 集団別評価、公平性、distribution shift | 母集団や集団ごとの失敗、変化と選んだ基準の妥当性 |
| adversarial robustness、prompt injection、privacy | 攻撃条件と情報・tool権限への影響 |
| 運用monitoring、incident対応、governance | 責任、停止条件、修正と再評価の証拠 |

## 6. 次の実験案（4本、すべて未実行）

1. **全閾値のROC/PRをsample IDから作る。** 既存fixtureの独立コピーについて、異なる全scoreを境界に`>=`の判定集合を列挙します。全陰性の端点は「最大scoreより大きい閾値」という数学上の条件として表し、既存runnerへ範囲外thresholdを渡しません。予想は閾値を下げるにつれて陽性予測集合が包含関係で増えることです。手書きID集合と各TP/FP/FN/TNを照合し、分母0のPR点を区別します。AUCを追加するなら同scoreのtieと積分規則を先に固定します。原典はGoogle ROC and AUCです。実モデル比較のcreditはありません。

2. **重複groupによるleakageを見える形にする。** 同じ原型から複製した合成入力をgroup ID付きで作り、行単位splitとgroupをまたがせないsplitを比較します。学習器の代わりに既知入力のlabelを返すlookup baselineを使い、未知入力の規則も固定します。予想は複製がtrain/testへまたがると見かけの評価が上がり得ることです。group交差・入力重複・予測IDを独立集合で照合し、scoreとsplitを記録します。原典はGoogle Dividing datasetsです。実学習や汎化の保証ではありません。

3. **同じ全体Accuracyでも内訳が違う合成集団を比較する。** A/Bの架空groupに同数のsampleを置き、各groupの陽性・陰性数を固定します。全体の正解数が同じでもFNが片方へ集中する2つの予測表を先に作り、group別の件数・Recall・FPRと全体値を照合します。予想は全体値がgroup差を隠し得ることです。陽性0件のgroupも別条件に加え、未定義を保持します。手書き混同行列をOracleにし、閾値やgroup構成を変えた結果を別表で保存します。Googleのmetric定義とNIST Map/Measureへ接続しますが、架空groupの差だけで現実の公平性や因果的差別を判定しません。

4. **生成応答の評価rubricそのものを試す。** 実モデルを呼ばず、合成の短い依頼と作者が書いた応答を12組用意します。無害な依頼への過剰拒否、回答の根拠不足、明示した情報境界の逸脱を区別する独自rubricを先に固定し、項目ごとの可否・対象外・判断不能を保存します。匿名化した2回の採点、または独立した2評価者の採点を比較し、不一致件をIDで列挙してから裁定します。予想は単一の「正答」値より項目別の失敗が見えることです。NIST Core Map/Measure/Manageは評価目的と対処の原典で、12件の数やrubricを規定していません。評価者一致や集計の動作を試す案であり、LLMの攻撃耐性・安全性試験を実施した扱いにはしません。

## 7. 資料の取得・検証状況

2026-10-05にGoogle ROC/AUC・Dividing datasets、NIST AI RMFの入口とCoreのHTML本文を取得して参照箇所を確認しました。今回取得不能だったURLはありません。既存2つのGoogle資料はsources.jsonのlocatorと教材の対応を読み、今回本文を再取得した資料とは区別しています。NISTページは1.0の改訂が進行中と記載しており、この文書は1.0の公開Coreを対象にします。第三者本文・図・モデル出力は保存していません。

追加したのはこの文書だけです。モデル学習・推論、集計runtime、checker、UI、global gateは実行せず、既存原票・QA・digestを更新していません。次実験の予想は新たな実測証拠ではありません。
