# OLSとholdout leakage：小さい誤差は公正な評価か

1特徴の直線`y = a + bx`をPython標準ライブラリで実学習する有限教材。train-only fit、holdout混入fit、holdoutによる候補選択を同じ固定合成点で比較する。係数とtrain／holdout MSEを分離し、学習直線・残差Plot・data lineageを操作UIで確認する。全Subjectの完了や現実予測性能は主張しない。

## 学習の道筋

**前提**：平均、直線の切片／傾き、二乗を理解し、`y−prediction`を1点で手計算する。高度な線形代数やMLライブラリは不要。

**概念と仕組み**：残差→残差平方和→OLS係数→MSEと進み、「計算した誤差」と「未使用の評価点」を別に考える。次に[実装と独立oracle](#実装と独立oracle)で同じ学習問題を別式から解く。

**実装・正常と異常**：[操作手順](#予想して操作する)で3経路と2点／一定xの境界を試し、[観測表](#固定入力と観測結果)へ戻る。

**実務判断**：fit／selectionの入力集合を記録し、選択へ使ったholdoutはvalidationと呼び直す。最終testを別に確保する設計が必要か判断できる。MSEの改善だけで「良いmodel」「leakageなし」を結論しない。

**限界から次へ**：1特徴toyでは、依存sample、前処理、相関する特徴、時系列の評価を扱えない。下の未実行4実験で広げる。理論・現実性能の保証には、その仮定と評価設計が別途必要。

**原典**：[一次資料locator](#一次資料locator)でOLS式と評価分離の根拠を確認し、UIの答え合わせで自分の説明と照合する。

## 次の4実験（全て未実装・未実行）

| 次の実験 | 問いと比較条件 | 今回からの接続／公式locator |
|---|---|---|
| N1：train / validation / testの3分割 | 固定3候補はvalidationで選び、未使用testで1回だけ評価すると、選択MSEとtest MSEはどう違うか。各rowの役割をoracleで確認する。 | 今回のholdout選択を評価設計へ直す。[公式§3.1導入](https://scikit-learn.org/stable/modules/cross_validation.html) |
| N2：前処理／feature selectionのfit範囲 | 固定2特徴の合成点でtrain-only selectionと全点selectionを比較し、test labelが選択へ流れるかを検査する。単なる1特徴OLSの平行移動でleakage効果を演出しない。 | 今回のfit lineageを前処理へ延長。[公式§12.2.2](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage-during-pre-processing) |
| N3：多変量OLSとrank／regularization | 独立な2特徴と完全相関した2特徴を比べ、正規方程式の解が一意か調べる。Ridgeを追加するならOLSと目的関数が異なることを検査する。 | 一定x拒否から識別可能性へ。[公式§1.1.1 OLS／§1.1.2 Ridge](https://scikit-learn.org/stable/modules/linear_model.html) |
| N4：時間順splitと未来の評価 | 固定の時間付き合成点で混合splitと過去→未来splitを比較。全fit indexが評価時刻より前か、gapを越えるか検査する。未来への一般化保証とは分離。 | 今回の範囲外点から依存・shiftへ。[公式§3.1.2.6](https://scikit-learn.org/stable/modules/cross_validation.html#cross-validation-of-time-series-data) |

ここでの候補実験は学習順の提案で、完了Artifactではない。新依存や実データの利用は次の割当で判断する。

## 予想して操作する

このdirectoryで起動する。既存listenerを止めず、OSに空きportを割り当ててもらう。

```sh
/usr/bin/python3 -B lesson.py --port 0
```

stdoutに出る`http://127.0.0.1:実際のport`を開く。終了は自分のterminalでCtrl+C。外部公開・依存installは不要。

1. 「正常：trainだけでOLS fit」を選び、このholdoutは学習・選択と独立か予想する。
2. 学習を実行。切片・傾き・残差と、MSEの分母に使う点を確認する。
3. データを変えず「train＋holdoutでfit」「holdout MSEで候補選択」へ切り替える。誤差だけでなくfit／selection row IDを比較する。
4. 「train 2点」の境界を試す。編集欄で一定xや空trainにすると拒否される。正常点へ戻せば回復する。
5. 原典・実装・独立oracleの式を読み、答えを開く。低いholdout MSEだけで未使用test性能を主張してよいか説明する。

入力変更時は旧結果を隠す。JSON parse拒否はbrowser側、一定x／空／型・範囲拒否はPython側。拒否後に古い成功図を新入力の結果として残さない。

## 固定入力と観測結果

`x/y`は中立な合成値。乱数も外部datasetも使用しない。

- train：`[[-2,-3],[-1,-1],[0,2],[1,3],[2,4]]`。
- holdout：同じx、trainのyへ2を加えた5点。
- 固定追加評価：`[[4,17],[5,26],[6,37]]`。既定train範囲外、関係は`y=x²+1`。コードはfit／候補選択へ渡さない。

| 経路 | 切片a / 傾きb | train MSE | holdout MSE | holdoutの役割 |
|---|---|---|---|---|
| train-only | `1 / 9/5` | `8/25 = 0.32` | `108/25 = 4.32` | 未使用testとして計算 |
| 混入fit | `2 / 9/5` | `33/25 = 1.32` | `33/25 = 1.32` | fitに使用済み |
| holdout選択 | `3 / 9/5` | `108/25 = 4.32` | `8/25 = 0.32` | 候補選択に使用済み |

選択反例は、train OLSの切片へ0/1/2を加える3個の固定線を比較し、holdout MSEが最小のoffset2を選ぶ。これら全候補がtrainのOLS最適解という意味ではない。比較はこの候補集合に限り、万能なmodel selectionの実装ではない。

選択経路の固定追加評価MSEは`6504/25 = 260.16`。このtoyの範囲外・別関係での誤差であり、現実の一般化誤差の推定ではない。正常経路でも一般化は保証されない。利用者がUIでholdoutや追加評価を見てmodelを選び直せば、その操作自体も評価情報の再利用になる。

追加評価の「OOD」は既定入力についての教材名。trainを編集するとx範囲が重なる場合があり、UIは現在のtrain範囲外点数を表示する。x範囲外というだけで全ての分布shiftを診断できるとは扱わない。

## 実装と独立oracle

[lesson.py](lesson.py)の`fit_ols(points)`は、明示して渡した点だけを使う中心化float式と`math.fsum`で学習する。[oracle.py](oracle.py)はproductionをimportせず、`Fraction`の正規方程式（2×2 determinant）で係数を解き、MSEと候補選択を独立に計算する。照合許容差はrelative `1e-10`、absolute `1e-9`。UIの2桁表示ではなく、未丸め値を照合する。

[test_lesson.py](test_lesson.py)はliteral係数・MSE、holdout label変更による正常係数の不変、125個の小datasetの正規方程式／最適性、並べ替え／affine response、2点境界、拒否→回復、OODのfit/selection不使用を検査する。MSEの分母はnであり、残差分散の不偏推定で使うn−2とは別。

正常経路の比較画面にも意図異常の2線を表示するが、各modelは別に学習している。正常modelのfit memberや係数へ他経路を混ぜていない。

## 検査と記録

既定checkerはread-only。原票更新は明示optionのみ。

```sh
/usr/bin/python3 -B verify.py
# 保存観測の再生成を求めた場合のみ
/usr/bin/python3 -B lesson.py --record
/usr/bin/python3 -B verify.py --record-checks
# 起動済みの自分のserverだけ
/usr/bin/python3 -B verify.py --record-http --port 実際のport
```

実IAB採取後にだけ`--record-media`を使う。`--record-readonly`は既定checkerを別processで実行し、前後のfile hashが不変であることを記録する。撮影機能はこのscriptにないので、空画像や想像図を実UI Evidenceへ差し替えない。

- [Python観測](observations/python.json)／[raw stdout](observations/stdout.txt)：実行時刻、CPython／OS、入力、data digest、source digest、3経路の係数・MSE・lineage。
- [試験ログ](observations/tests.txt)／[binding](observations/checks.json)。
- [実HTTP生応答](observations/http.json)、[実UI DOM](observations/ui-dom.json)、[6 JPEGのdigest・寸法](observations/media.json)、[read-only検査](observations/readonly.json)。
- [Skill](skills/atlas-data-science-statistical-learning/SKILL.md)／[ローカルrouting review](observations/skill-review.md)／[owned resource終了](observations/cleanup.md)。

背景IAB desktopで実操作・実画面を採取。browser engine版はツールに公開されず不明。mobile、動画、別OSは未検証。Skill reviewは自己レビューで、独立Agent Evalではない。

## 一次資料locator

2026-10-05に本文を確認。第三者本文や図は保存・複製しない。

- [NIST e-Handbook §4.4.3.1](https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd431.htm)、`LS for Straight Line`：残差平方和の最小化と、中心化した傾き・切片の式。oracleでは同じ問題を正規方程式から別計算する。
- [scikit-learn公式 §12.2 Data leakage](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage)、§12.2.1：testとtrainを分離し、testをfit・選択に使わない境界。閲覧時の文書headerは1.9.1。ライブラリは実装依存ではない。
- [公式 §3.1 Cross-validation](https://scikit-learn.org/stable/modules/cross_validation.html)、導入／model selection：modelを選ぶためのvalidationと最終評価のtestを分離する。本教材でCV自体は実装していない。

## Subject内のCoverageと未教材領域

この有限教材だけでは以下の未教材領域を埋めない。分類の追加余地も残し、全分野denominatorが閉じたとは主張しない。

| 領域 | 状態／次に問うこと | 学習入口 |
|---|---|---|
| 1特徴OLS、MSE、leakage | 実装。何をfit／選択へ渡したか？ | 本教材とN1 |
| 多変量回帰、GLM、classification | 未教材。特徴が増えたとき解・lossはどう変わるか？ | N3、[公式§1.1](https://scikit-learn.org/stable/modules/linear_model.html) |
| regularization／optimization／conditioning | 未教材。最適化の目的と解の安定性を変える条件は？ | N3、公式§1.1.1／1.1.2 |
| preprocessing／欠損／feature engineering | 未教材。変換器はどの集合でfitしたか？ | N2、[公式§12.1–12.2](https://scikit-learn.org/stable/common_pitfalls.html) |
| feature selection／hyperparameter | 未教材。testを繰り返し選択へ使っていないか？ | N1/N2、公式§3.1導入 |
| validation／CV／nested CV | 未教材。選択の外側の評価集合を残せるか？ | N1、[公式§3.1／§3.2入口](https://scikit-learn.org/stable/user_guide.html#model-selection-and-evaluation) |
| 時系列／group split | 未教材。sample間の依存をsplitが跨いでいないか？ | N4、公式§3.1.2.4／3.1.2.6 |
| bias/variance／学習曲線 | 未教材。点数増加でtrainと評価誤差の差は変わるか？ | [公式Guide§3.5](https://scikit-learn.org/stable/user_guide.html) |
| probabilistic／Bayesian learning | 未教材。点予測ではなく分布をどう評価するか？ | [公式Guide§1.1.10／1.7](https://scikit-learn.org/stable/user_guide.html) |
| clustering／次元削減／density | 未教材。labelなしの目的をどう定義・評価するか？ | [公式Guide§2](https://scikit-learn.org/stable/user_guide.html) |
| trees／ensembles／kernel／deep learning | 未教材。表現力を増やすと評価設計はどう変わるか？ | [公式Guide§1.4／1.10／1.11／1.17](https://scikit-learn.org/stable/user_guide.html) |
| uncertainty／calibration／interval | 未教材。MSEだけでは分からない予測の不確実性は？ | [NIST§4.4.3.1・Quality of Least Squares Estimates](https://www.itl.nist.gov/div898/handbook/pmd/section4/pmd431.htm)、[公式Guide§1.16](https://scikit-learn.org/stable/user_guide.html) |
| distribution shift／robustness | 未教材。評価分布と利用時の分布は同じか？固定追加評価だけで判定しない。 | N4、公式§3.1.2.6 |
| causal inference／experiment design | 未教材。相関予測から介入効果を結論してよいか？ | 回帰を因果と扱わない。次回は専門一次資料を選ぶ必要がある |
| explainability／fairness／privacy | 未教材。説明対象・集団別誤差・個人情報の扱いをどう分離するか？ | [公式Guide§5 Inspection](https://scikit-learn.org/stable/user_guide.html)、fairness/privacy専用資料は次回選定 |
| data quality／real dataset／運用monitoring | 未教材。欠損・lineage・失効・再学習をどう検証するか？ | N2/N4、[公式Guide§8.4／§11](https://scikit-learn.org/stable/user_guide.html)、運用資料は別途必要 |

Portal root文書、旧Atlas、Core/Graph、公開設定をこの教材で変更しない。物理／外部Runtimeや実運用予測を代替していない。
