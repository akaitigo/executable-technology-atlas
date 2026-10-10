# 「95%区間」は、n=8で何%を覆う？

[既存LEARNING_PATH実験2](../../../subjects/mathematical-statistical-foundations/LEARNING_PATH.md)の追加単元。既知counts/Bayesで分母を確かめる前提から、独立Bernoulli標本の点推定と区間手続きへ進みます。原入口97件、旧source/raw/coverage/QAは変更しません。

## 前提と入力契約

分数・確率の重み・独立な8回の成功/失敗を読めることが前提。nはboolではない整数8、true pはdecimal文字列0.1/0.5/0.9、zは文字列1.96のみ。bool、NaN/Infinity、契約外n/p/zの7inputは拒否し、計算成功3件と別に記録します。

推定値 p_hat=k/8。通常Wald式は `p_hat ± 1.96 sqrt(p_hat(1-p_hat)/8)`。1.96は指定した丸めcritical値で、正確なnormal quantileではありません。nominal95%は正規近似手続きの名称。区間を[0,1]へclippingせず、外へ出る端点も残します。k0/8の区間は[0,0]/[1,1]で幅0です。

## 予想 → 操作 → 正常/境界/拒否比較 → 原典/raw → 答え

[画面](index.html)で条件と予想を選び「保存計算を比較」。kを変えて同じ手続きの9区間を確認し、真pを含むk・二項mass・加重coverageを読む。k0/8、外へ出る端点、拒否inputを比較し、[実装](calculate.py)、[独立checker](checker.py)、[契約](contracts.json)、画面run原票へ戻り答えを開きます。画面は保存した計算結果の表示で再計算/random samplingではありません。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
# 新原票採取を明示したときだけ
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record
python3 -u -m http.server 0 --bind 127.0.0.1
```

表示された動的portへ接続、Ctrl-Cで所有serverを終了。通常checker/routeと引数なしrunnerは更新しない。引数なしrunnerのexit1は更新拒否。明示recordは新runのcommand/time/exit/stdout/stderr/input/runtime/source/原票artifact SHA256を保持し、旧rawを上書きしません。child timeout5秒、実行失敗はcommandを残してpointerを変えません。Node PID3901/port53478は触りません。

## 2つの導出と手計算

producerはk0..8の9項 `C(8,k)p^k(1-p)^(8-k)` をDecimal precision40/HALF_EVENで計算し、Decimal sqrtによる端点が真pを含む項だけ加重。有限入力のmass/coverageは正確な有限小数、平方根端点は近似です。

独立oracleはproducer・comb・sqrtを使わず、256の0/1列を全列挙。各列のFraction重みを積み、`(p-k/8)^2 <= (49/25)^2 (k/8)(1-k/8)/8` で包含を判定。massの合計1、covered集合、coverageを検算し、平方不等式で端点計算も別に照合します。端点の平方残差等の許容値は1e-36で、包含の判断そのものはexact Fractionです。理論的全列集計をrandom sampleや実データ性能と呼びません。

別の手計算：p=.1はk1/2/3で、mass=.38263752 + .14880348 + .03306744 = .56450844。p=.9は成功/失敗対称でk5/6/7、同じ値。p=.5はk2..6の列数28+56+70+56+28=238、全256列なので238/256=119/128=.9296875。これらは実行前に固定し、独立列挙と照合します。

| true p | covered k | exact coverage | nominal95%との差 |
|---|---|---|---|
| .1 | 1,2,3 | .56450844（14112711/25000000） | −.38549156 |
| .5 | 2..6 | .9296875（119/128） | −.0203125 |
| .9 | 5,6,7 | .56450844（14112711/25000000） | −.38549156 |

この表は事前手計算。実計算と独立oracle/実IABの結果は[QA](qa/README.md)へ。

## 実務判断と単一観測

未知のpは固定した母数で、観測前に区間手続きが標本によって変わります。coverageはこの手続きが同じ条件を繰り返した時に真pを覆う確率です。今回は全標本空間を重み付きで計算しました。

観測kが固定された後、得た具体区間は真pを含むか含まないかです。「この区間に真pが95%の確率で入る」というposteriorの主張へ置き換えません。真pが既知なのはcoverageを検算する教材上の設定で、現実の推定で真pを入力できることを意味しません。

n8のk0/8で幅0になっても母数が確実に0/1とは言えません。区間の幅だけで質を判断せず、手続き・sample size・独立性・対象population・coverageを確認します。選択bias、依存、実データ、医療等の個別推奨は評価しません。Wald手続きの弱さを示しても、代替区間が常に最適だとは主張しません。

## 原典locatorと未教材

[Probabilitycourse §8.3.0](https://www.probabilitycourse.com/chapter8/8_3_0_interval_estimation.php)は点推定から区間幅/confidence levelへ進む導入。[NIST7.2.4.1](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)の通常confidence expressionが今回のWald式、負下限の指摘がclippingなしの境界へ接続します。NISTページの主なWilson式とexact binomial区間は今回は実装していません。[sources.json](sources.json)に取得日/locator/binding/取得不能の誤URLを保存。本文/画像を転載しません。

増分はBernoulli標本→推定値→区間手続きの理論coverage、degenerate/範囲外端点、単一観測と反復coverageの区別です。全Subject/Atlas完成やformal delivery/global gateは主張しません。

次3実験は提案・未実行で、自動開始しません：

1. 同じn8/k0..8へWilson区間を別実装し、256列oracleでWaldとの差を比較。NIST7.2.4.1 Wilson式。bounded endpointだけでcoverage保証とはしない。
2. exact binomial区間を有理mass+有限root bracketで導き、許容誤差と保守的coverageを検算。NIST7.2.4.1 Exact Intervals for Small Numbers。exactという語と数値solver精度を分ける。
3. 独立性を外す小さな明示joint分布で同じn8区間を比較し、Bernoulli積の重みを使い続ける誤りを示す。Probabilitycourse§8.3.0のrandom sample前提へ戻る。実データの依存推定は別。
