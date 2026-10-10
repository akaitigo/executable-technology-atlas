# Randomized response・差分プライバシーのcompositionを学ぶ

問いは「1回答の確率比bound3を、独立2回答にもそのまま使えるか」です。Privacy engineeringのLEARNING_PATH §6実験4だけを扱い、個人情報のない合成1bit入力0↔1で全coin経路を厳密計算します。

[元Subjectの学習の道筋](../../../subjects/privacy-engineering/LEARNING_PATH.md)の§6実験4を具体化しました。[識別子除去・群計算の既存教材](../../../subjects/privacy-engineering/README.md)とは異なる確率的機構です。読む順番は元の道筋→この前提→UIの予想と分布→原典/実装/raw→答えと実務判断です。既存教材はこの単元では再実行していません。

## 前提 → 予想 → 操作

確率、Fraction、直積、出力event集合を前提とします。branch coinとanswer coinは公平・独立。branch0なら真実、branch1ならanswer coinを返します。第2coinが使われない真実branchも2経路に分けるので、1回答は4同確率経路。2回答は同じbitについて4coin、16経路です。

1. 単元directoryで `python3 checker.py`。保存原票を手書き期待表と独立Fraction直積oracleへ照合します。
2. `python3 -m http.server 0 --bind 127.0.0.1 --directory ../../..`。元教材への相対リンクも読めるlearning rootをread-only配信し、動的portの `/continuations/privacy-engineering/randomized-response-composition/index.html` を開き、条件・予想を選び「比較する」。所有serverだけ終了します。
3. 全出力分布、両方向比、正常boundと故障版claimを比べ、経路/eventの詳細と答えを読む。条件変更は予想もreset。予想変更は選択値を保持し旧結果・答えをclearするので、再度比較します。
4. 新実測は明示 `python3 runner.py --record`。新observationsを作り、古い原票を保全してUI pointerを更新。通常runnerは書かずexit1で案内。

予想は同答3/4・反答1/4、1回答max比3、独立2回答max比9。2回答のmarginalは各々同じ比3でも、joint00/11で比9になるため、bound3の流用は通りません。

## 事前手書き表と正常/故障対照

`expected-distributions.json`はproducer実行前に固定。

| 出力 | 入力0の1回答 | 入力1の1回答 |
|---|---|---|
| 0 | 3/4 | 1/4 |
| 1 | 1/4 | 3/4 |

| joint出力 | 入力0の2回答 | 入力1の2回答 | 0側/1側の比 |
|---|---|---|---|
| 00 | 9/16 | 1/16 | 9 |
| 01 | 3/16 | 3/16 | 1 |
| 10 | 3/16 | 3/16 | 1 |
| 11 | 1/16 | 9/16 | 1/9（逆は9） |

正常版はjointの全非空event集合15件（1回答では3件）、両方向を検査しbound9/3内。故障版は最初の回答のmarginal max比3だけを計算して「bound3内」とclaimします。そのclaimをjoint eventへ照合すると2回答ではsingleton00/11の2eventで違反。小さい一回のboundをjointへ流用する判定漏れを実計算で示します。空eventは両確率0で、不等式0≤bound×0を満たし、比0/0は作りません。

入力契約はanswersがboolを除くint1/2、coin_profile='fair-independent'のみ。bool/floatのanswers、3回答、correlated profile、field欠損の5入力は分布生成前にexpected refusal。拒否はprivacy検査合格ではありません。

## ratioとepsilonを区別する

原典[Dwork & Roth](https://www.cis.upenn.edu/~aaroth/Papers/privacybook.pdf) Definition2.4は、隣接入力の全eventについて確率をexp(epsilon)とdeltaで比較します。今回は独自に隣接を1bitの違いとし、delta=0で比bound3ならepsilon=ln(3)、bound9ならepsilon=ln(9)=2ln(3)です。epsilon=3/9とは書きません。logは記号表示で、丸めたfloatから厳密boundを決めません。§3.2はrandomized response、§3.5/Corollary3.15は繰返しcompositionへの接続です。

この有限機構は、指定した1bit隣接と全出力eventに対する分布不等式を検算しています。一般DBの隣接・accountant・既存12件releaseのDP化・実サービスのprivacy保証へは拡張しません。

## 原典・実装・rawと独立oracle

calculate.pyはcoin path全列挙からFraction質量を集計。rawに全経路、pathmass、分布、singleton/全event両方向比、boundary違反、正常判定とmarginal故障claimを保存。乱数module・seed・random samplingは使わずsamples=0です。

checker.pyはproducerをimportせず、手書き3/4・1/4から独立Fraction直積でjointを作り、手書き9/16等へ照合。producerのmask列挙とは別のcombinationsで3/15eventを列挙し、全質量・両方向max・空eventを除く境界を検算します。全coin tupleと手書き4経路mappingも照合し、自己一致だけにしません。5つのin-memory故障原票を検出し、rawを変更しません。

runnerは実command stdout/stderr/exit、runtime、source/artifact hashを保存。UIは保存原票の比較で、閲覧時の新計算ではありません。[QA](qa/README.md)に実IAB/capture/read-only証拠。Skillはskills/atlas-randomized-response-composition/SKILL.md。正常6/未対応4routeは構造検査のみ、モデル挙動評価は未実行。

## 答え → 実務判断

同じ保護対象への複数releaseは別々にprivacyを使います。一つずつのmarginalだけでなく、受取者が見られるjoint出力と隣接・独立性・release回数を明示して予算を判断します。ここで比9に達するeventがあることは、特定の実人物を再識別した証拠ではありません。

## 次coverage（未実行）

1. QI追加と群内category同質性を架空表で手集計。kと属性情報を分ける。
2. drop/generalize/countで4用途のutilityを比較し、計算不能と誤差を分ける。
3. 合成2時点category count差分と追加1record仮定で、推論可能/不能を比較。

一般DB/accountant・実person・外部linkage・実サービス保証、Core/fullGate/commit/push/公開は未実行。分野全体・Atlas全体のcompleteを主張しません。
