# ML第2単元：標準化はどのsplitからfitするか

[第1単元：schema/version付き固定model推論](../../../subjects/machine-learning-systems/README.md)の次に学ぶ教材です。第1単元は入力の意味を合わせました。今回は**同じfeature契約でも、変換をfitする範囲が意味と距離を変える**ことを実Pythonで検証します。既存moduleを変更せず、この単元だけで実行できます。

## 前提 → 主要概念・仕組み

2D数値、平均/母分散、平方距離、JSONとtrain/heldout splitを前提にします。主要概念はfitとtransform、leakage、zero variance、1NN、parameter artifact、cohort不変条件。自作stdlibのscalerが `mean=sum/n`、`variance=sum((x-mean)^2)/n` をfitし、`z=(x-mean)/sqrt(variance)` でtrain/queryをtransform。分散が厳密に0の列はscale1。trainだけのlabel付き行を標準化後に記憶して1NNmodelをfitし、平方Euclidean距離最小でpredictします。完全同距離はtrain行順の先頭です。

正常 `train-only` はtrain featureだけでscalerをfit。意図異常 `leaked` はtrain+heldout featureでfitします。**どちらも1NNのlabelとneighborはtrainだけ**で、漏洩版もheldout labelを使用しません。未知version/feature順、bool/nonfinite、空train/heldout、次元不正、重複split ID、heldout labelをfit前に拒否します。feature契約は `xy-v1`, `[x,y]`、最大32行/split、値の絶対値1e6以下。zero varianceを拒否するのでなく、scale1という明示した境界動作を検証します。

## 予想 → 操作 → 正常/意図異常比較

[画面](index.html)は保存した実fit原票を読みます。ケース・fit方針を切替え、traceを前後へ進めて予測と照合します。先に予想：trainもqueryも同じなのに、別heldout行の追加で同queryの予測が変わるか？ 同じ変換をtrain/queryに適用すればfit範囲は問わなくてよいか？

固定trainは `(0,0)→A, (10,1)→B`。queryは `(6,0)`。small heldoutはquery1行、expandedはqueryに `(0,100)` を追加。期待値は実装前に[不変手計算表](hand-oracle.json)へ固定しました。

|fit|small平均/分散|expanded平均/分散|query平方距離A,B / 予測|
|---|---|---|---|
|train-only|[5,1/2] / [25,1/4]|同じ|[36/25,116/25] / A（両cohort）|
|leaked|[16/3,1/3] / [152/9,2/9]|[4,101/4] / [18,29803/16]|small [81/38,207/38] / A、expanded [2,238568/268227] / B|

heldout外れ値がy分散を膨らませ、その方向の距離penaltyを弱めるためBが近くなります。標準化後座標のfloat実計算と、独立Fractionの**元座標差²/variance**を照合します。独立oracleは本体validator/fit/transform/predict/sqrtを呼びません。

zero-varianceではtrain/queryのyを1に固定し、scale1、予測B。tie query `(5,.5)` はA/B同距離、先頭Aです。10拒否case×2方針と100seed固定cohort pair×2方針で境界・不変条件を検査します。

## 実務判断 → 限界

train固定なら正常parameterと同query距離/予測がheldout cohortに依存しない、という条件を判断できます。正常small/expandedのparameter SHA-256は一致、漏洩版は相違します。全split行、fit行ID、mean/variance/scale、train transformed model、query transformed、距離、予測、fit UTCを記録します。hashは同一bytes/parameterの確認で、正しさ/信頼/承認を単独で証明しません。

架空2D小データの反例です。**heldout labelとaccuracyを持たず、性能/統計的汎化/精度の改善は保証しません**。scikit-learn/TFXを実行せず、stdlib自作実装のfitです。任意k、欠損/疎matrix、近ゼロ分散の安定化、極端値の数値誤差、実データ、CV、hyperparameter search、配信/監視/rollbackは未教材です。float平方距離は丸めを含み、今回検証vector以外の極小差tie順序を保証しません。

## 原典 → 実装 → 答え

[source bindings](sources.json)はscikit-learn Common pitfalls §12.1–12.2のfit範囲、StandardScalerのmean/var/zero variance/ddof0、Neighborsの距離とtieを今回実装へ対応させます。ライブラリ互換を主張せず、原典の原則と本体の選択を分けます。

答え：train/queryが同じでも、漏洩版はheldoutの別行だけでA→B。正常版はparameter/距離/予測が不変。「同じ変換を適用する」ことに加え「その変換をtrainだけからfitする」ことを守ります。

[実装](preprocessing.py) / [checker](verify.py) / [全固定入力](fixtures.json) / [raw](observations/raw.json) / [学習parameter artifact](observations/fitted-parameters.json) / [receipt](observations/receipt.json) / [検証記録](VERIFICATION.md)。

```sh
python3 verify.py --record  # 初回原票。明示更新のみ
python3 verify.py           # file read-only再fit/照合
python3 serve.py            # dynamic127.0.0.1、後でCtrl-C
python3 route.py preprocessing
python3 route.py production-train
```

fit UTCは毎回変わるため通常checkerはsemantic結果とparameter digestを照合し、原票を書き換えません。実UI観測後は `--seal-record` でrawを保持してreceiptだけ明示更新します。作者Skill validation/routing smokeは独立AgentEvalではありません。

## 今回増えたcoverageと残る未教材

[coverage](coverage.json)はSubject9領域をつなぎます。今回feature/preprocessingに実fitとleakage反例、学習再現に固定splitとparameter artifact、推論にlocal1NNを追加しました。第1単元のschema契約と合わせて入力→fit→transform→predictまでを理解できます。元moduleのcoverage/未実行案はread-onlyのまま、後の統合で扱います。

取得/lineage、品質評価/承認、registry、負荷serving、drift/再学習、配信/復旧、trust/privacy/resourceは依然未教材。各領域を具体的概念・問い・原典に対応しました。次3本は①合成label付きslice評価gate、②固定CV fold内fitと全体fit、③model/schema/transform bundleのatomic rollback。判定可能なことを一段ずつ増やします。
