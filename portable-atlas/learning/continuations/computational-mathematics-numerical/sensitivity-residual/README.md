# 感度と残差を分ける

[元Subject学習パス](../../../subjects/computational-mathematics-numerical/LEARNING_PATH.md) §5実験1の有限継続教材。既存の総和教材を読んで、十進数の意味とfloat変換の差を確認してから進む。[関連：performance/capacity教材](../../../subjects/performance-capacity-engineering/README.md)は測定とその基準を扱う。今回の感度観測を性能保証に転用しない。

前提は分数・二進float・絶対値・2行の連立方程式・Pythonのlist/関数。読む順番は数学的入力→floatで作った入力→実消去法→2つの厳密解→誤差/残差→条件数→実務判断。UIは予想→εや故障判断の変更→実行→正常/異常比較→一次仕様/コード/raw→答え、の順。

## 固定問題と事前期待

A=[[1,1],[1,1+ε]]、元x=[1,1]からb=[2,2+ε]。b₂だけδ=1/1000000を加える。十進入力を厳密Fractionで解くと変化は[-δ/ε,+δ/ε]。

| 条件 | 十進厳密な摂動後解 | 元xからの最大変化 | その系の残差 / 元の系の残差 |
|---|---|---|---|
| ε=1/10 | [99999/100000,100001/100000] | 1/100000=1e-5 | [0,0] / [0,1/1000000] |
| ε=1/10000 | [99/100,101/100] | 1/100=1e-2 | [0,0] / [0,1/1000000] |
| bad-residual-only | ε=1/10000と同じ実solver | 残差小⇒元xに1e-6以内とする故障規則を反証 | solver故障ではなく基準を混同した判断 |
| singular-refusal | ε=0は固定入力契約外 | solver_started=false | 特異系を解かず事前拒否 |

正常2、故障判断比較1、期待する契約拒否1を別に数える。oracle.jsonは実行前に手書き。特異の解法は実装していない。最大の解変化はこの固定2条件の比較であり、全入力の最大誤差ではない。

## 実計算・2oracle・norm

solver.pyはfloatの2×2消去/後退代入を実行する。Aの1+εをfloatで作り、元xから各行の内積でb_originalを作り、floatδを加える。baselineと摂動後を同じ手順で解く。reference.pyはsolverをimportせず、FractionのCramer閉形式で以下を別に求める。

- 十進文字列の数学的A/bの厳密解。
- 実float A/bの各値をFraction.from_floatで正確に取り込んだ系の厳密解。εだけをFraction化する代用品にはしない。b生成/δ加算後の丸めも入力に含む。

vector ∞normは最大絶対成分、matrix ∞normは絶対行和の最大。入力変化∞norm/元b∞norm、baseline解からの変化∞norm/baseline解∞norm、元xとの距離を別に表示。十進κ∞=(2+ε)²/ε（44.1 / 40004.0001）、この方向の相対増幅は(2+ε)/ε（21 / 20001）。κは上限、今回の方向の増幅と同一ではない。

forward errorは計算した摂動後解から各「摂動後oracle解」を引く∞norm。元xとの距離は感度による問題変更を含み、forward errorと呼ばない。oracle同士の差も記録する。FNC Definition 2.8.2の残差はb−Axで、教材は符号を反転したAx−bを使う。∞normは同じ。残差はAx−bを符号付きで、元系と摂動後系を分ける。floatで評価した残差と計算解をFraction化して厳密再評価した残差も別に保持。float残差0を厳密な0と呼ばない。十進厳密な摂動後解は、その系で厳密残差0。

実Mac Python3.9.6ではfloat摂動後残差[0,0]、元系残差は約[0,1e-6]。元xとの距離は約1e-5/0.01。小さいεでは十進oracleへのforward error約8.22e-13、実float入力oracleへ約8.88e-18。これを任意solverの安定性保証にしない。

## 再現と証拠

このdirectoryで `python3 -B runner.py --case epsilon-0.0001`。fresh原票保存は明示 `python3 -B runner.py --record` のみ。採用原票はobservations/20261005T122820900176Z/raw.json（command exit0）。UTC/runtime/入力/実float行列・b/計算解/trace/2Fraction解/各残差/5source SHAを保存。

`python3 -B check.py` はproducer/referenceをimportせず、十進閉形式・手書き表・実float入力の厳密方程式と非特異性、norm・2forward error・残差を照合する。独立Cramerが出した解が実入力の方程式を厳密に満たすことを検査し、5種の意味ある改変を拒否。通常check/Skill routeはhash/mtime不変。画面は `python3 -B server.py` の127.0.0.1:0専有previewから実Pythonへ問い合わせる。case変更とprediction変更は結果/trace/raw/答えをclear、prediction変更は新値を保持、generationで旧応答を破棄。拒否も前の正常結果を残さない。

## 一次資料・実務判断・限界

Driscoll/Braunの著者教材[FNC §2.8 Conditioning of linear systems](https://fncbook.com/condition-number/) Definition 2.8.1 / Theorem 2.8.1を2026-10-05確認。normと条件数、入力摂動と解変化の関係を参照した。生きたページのlocatorで、例やコードの転載はしていない。

実務では入力精度、正本にする系、基準解、normと許容値を明示し、残差・感度・計算誤差を別に判断する。安定なsolverでも入力誤差に敏感な問題はある。この固定2×2だけで任意solver安定性、pivoting/大規模分解/疎行列/性能/GPUを保証しない。Core/fullGate・依存追加・commit/push・公開・設定変更は未実施。Subject/Atlas全体の完了ではない。captureは実ツール画面表示で、画像未保存の場合QAに正直に記録する。

## 次の未実施案

1. 同じ固定2×2で別計算順序/pivotingを比較。入力oracleを共通にして計算誤差の増幅を調べる。[FNC Stability](https://fncbook.com/stability/)を参照。任意solver安定性は現単元では未実証。
2. A自体の1要素も摂動し、b摂動と分ける。各正本に対するoracle/残差/forward errorを比較。FNC §2.8 Theorem 2.8.1の行列摂動を参照。現単元はA固定。
3. 二次式の離れた2根で解公式と積からの再計算を比較。係数float変換後の根oracleと元根を分ける。元学習パス§5実験2/FNC Stabilityのcase studyへ戻る。現単元では未実施。
