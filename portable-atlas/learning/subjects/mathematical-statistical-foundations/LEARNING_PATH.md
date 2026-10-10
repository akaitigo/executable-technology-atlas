# 数学・統計の基礎を、分母の確認から広げる

この文書は既存の [README](README.md) を置き換えない補足ガイドです。既存教材の実装・原票・検証記録を変更していません。以下の学習計画は新しい実行証拠ではありません。有限教材の補足であり、分野全体の学習完了を示すものではありません。

## 1. 前提を手で確かめる

分数、割合、集合の共通部分、表の行列を読めれば始められます。まず12要素の例で A+ = 2、A− = 1、B+ = 3、B− = 6 と置き、全体12、A集合3、test+集合5を数えてください。交差部分が同じ2でも、2/3と2/5は違います。式を覚える前に「どの集合から1要素を選ぶか」を言葉にします。

実装まで読む場合はPythonの関数、整数、dictが前提です。Fractionは整数の比を正確に保持する道具で、画面の百分率や点の座標とは精度が異なります。

## 2. 主要概念の見取り図

集合と数え上げ → 同時確率 → 条件付き確率 → 全確率とBayes → 標本からの推定、の順に進みます。今回実装しているのは全populationを知っている前半です。

条件付き確率は条件集合を分母にします。Bayesは逆向きの条件を、元の条件付き確率とprior、観測の総確率から求めます。条件集合が空なら未定義であり、確率0とは分けます。さらに先には、確率変数・期待値・分散・分布、推定・検定、行列・線形変換、最適化、因果の問題があります。確率を正確に計算できることと、現実の率を正しく推定できることは別です。

## 3. 今回の正常・境界を読む

[画面](index.html) → [READMEの観測表](README.md) → [実装 lesson.py](lesson.py) → [Python原票](observations/python.json) → [生stdout](observations/stdout.txt)の順で辿ります。起動方法はREADMEにあります。この補足作業では起動していません。

感度9/10、偽陽性率1/10を固定して、Aの割合1%と50%を比較してください。PPVはそれぞれ1/12と9/10です。「感度90%ならPPVも90%」という逆転した推論を比べる教材であり、計算器に意図的な誤実装を追加した実験ではありません。test+なしではPPV未定義、Aなしでは感度未定義でもPPVは0です。これらの違いを分母で説明します。

## 4. 実務で判断できることと限界

率を比較する時は分子・分母・条件・対象populationを併記する、感度だけから逆向きの確率を結論しない、空集合を0へ置換しない、という判断に使えます。priorが既知populationの割合か、未知母数についての仮定かも分けてください。

今回の合成countsにはsamplingも未知母数推定もありません。現実の検査精度、選択bias、因果効果、医療等の個別判断、連続分布、理解度は評価していません。図の百分率は近似、Fractionが正本です。

## 5. 未教材の概念を問いにする

| 主要未教材 | 次に説明したい問い | 学習上の接続 |
|---|---|---|
| 確率変数・期待値・分散・標本 | 同じ母集団から取った標本で、推定値が揺れるのはなぜ？ | countsを既知とする今回の仮定を外す |
| 点推定・区間推定・検定 | 点推定だけで精度を言える？ 区間の被覆率と、得た1区間の解釈は同じ？ | 次の実験2へ。検定・多重比較はさらに別教材 |
| Bayesian inference・未知prior | 未知の割合の候補へ、観測でどんな重みを付ける？ | 次の実験1へ。連続posteriorは別教材 |
| 線形代数・固有値・分解 | 行列は何を変換し、繰返し適用するとどの方向が残る？ | 次の実験3へ。QR/SVD等は別教材 |
| 連続分布・積分・条件付け | 密度の高さを、その点の確率と呼べる？ | 有限countsの外。専用原典と実験は未選定 |
| 最適化・因果・実データ | 何を最小化する？ 相関から介入効果を結論できる？ | 専用原典・実験は未選定。Bayesの計算で代用しない |

## 6. 次の3実験（すべて未実装・未実行）

1. **有限仮説のBayes更新**：coinの未知確率候補を1/4と3/4、priorを1/2ずつに固定し、3回中表1回という同じ観測で更新する。尤度と正規化後の重みをFractionで計算し、観測と仮説の同時確率表から別に照合する。その後priorだけを変え、posteriorの変化を観測する。既知populationの割合から未知母数の仮説へ進む実験。原典は著者教材 [§1.4.3 Bayes' Rule](https://www.probabilitycourse.com/chapter1/1_4_3_bayes_rule.php)、分割事象に対するBayes式。
2. **区間の被覆率**：独立Bernoulli、n=8、真のp=0.1/0.5/0.9を固定する。各成功数kの推定値k/nと正規近似区間を作り、k=0..8の二項確率で重み付けして、真のpを含む率と区間幅を比較する。k=0/8で幅が0になる近似の境界も残す。「95%」という名称だけで有限nの被覆率を保証しない。原典は著者教材 [§8.2.0 Point Estimation](https://www.probabilitycourse.com/chapter8/8_2_0_point_estimation.php) と [§8.3.0 Interval Estimation](https://www.probabilitycourse.com/chapter8/8_3_0_interval_estimation.php)、点推定・区間幅・confidence levelの導入。具体的な区間式の導出と二項分布oracleは次実装時の追加課題。
3. **2次元の行列と固有方向**：対角行列diag(2,1)と回転行列を、同じ初期ベクトルへ有限回適用する。座標、長さ、方向、固有ベクトル候補についてAv=λvの残差を比較する。回転が実固有方向を持つと決めつけない。原典はMIT公式 [Eigenvalues and Eigenvectors](https://ocw.mit.edu/courses/18-06sc-linear-algebra-fall-2011/pages/least-squares-determinants-and-eigenvalues/eigenvalues-and-eigenvectors/)、Session Overview・Lecture 21・Suggested Reading §6.1–6.2。

3本でも数学・統計全体は閉じません。実験の入力・oracle・観測を新たに用意する必要があります。

## 7. 原典の確認状況

新規locatorは2026-10-05にread-only webで上記著者教材§8.2.0/§8.3.0とMIT公式sessionを確認しました。既存Bayes locatorも再確認しました。本文・画像・コードは転載していません。

探索時の `https://www.probabilitycourse.com/chapter6/6_1_1_point_estimation.php`、`https://www.probabilitycourse.com/chapter9/9_1_1_intro.php`、`https://www.probabilitycourse.com/chapter8/8_1_0_statistical_inference.php`、`https://web.mit.edu/18.06/www/Spring17/` はweb toolで取得できず、根拠には使っていません。取得不能を文書不存在とは断定しません。既存原典の取得履歴は [source-access.md](observations/source-access.md) を参照してください。

この追加で実験・runtime・実UI再QAを実施したとは主張しません。既存証拠のhashやsource束縛は再封印していません。
