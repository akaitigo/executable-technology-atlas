# Atlas｜有限Bayesの原典と既存教材

2026-10-06に著者公開本文を読みました。本文・図・コードを転載せず、狭い式と条件を今回の模型へ対応付けます。

- H. Pishro-Nik著教材 [§1.4.3 Bayes' Rule](https://www.probabilitycourse.com/chapter1/1_4_3_bayes_rule.php)：分割事象に対する式と、観測確率が正という条件。二つのp仮説のprior×likelihoodを正規化する根拠です。
- 同 [§3.1.5 Binomial Distribution](https://www.probabilitycourse.com/chapter3/3_1_5_special_discrete_distr.php)：BinomialのPMFと独立Bernoulliの和。個数観測の組合せ係数を、特定の一列の確率と区別します。



重複読取では次を確認しました。

- 元README52行：既知populationの割合と、未知母数のprior/posteriorを明示的に区別し、後者は対象外。
- small-sample-interval-coverage README44行、wilson-wald-finite-coverage README46行：区間手続きの被覆率を扱い、得た区間のposterior解釈をしない。前者でCOVERAGE.mdは見つからず、READMEを根拠にしました。
- 既存DOE、control-noise、管理限界、measurementの6追加単元は別の問い。元LEARNING_PATHの「すべて未実装」を現在の分野全体へ転用しません。
- QE COVERAGEの「有限Bayes」は元の条件付き確率教材へのリンクです。AI基礎・統計学習のREADMEはBayesian inferenceを未教材としますが、それだけで現在の全成果の不存在を断定しません。

確認範囲はcatalog snapshot、post90受入queue、現在の独立reconciliation、元learningのREADME/COVERAGE、独立教材のREADME/COVERAGE/受入記録です。この範囲では二つの未知p仮説の更新を実装した教材は見つかりませんでした。元ownerの現在状態は未確認のまま、独立pathだけを制作します。
