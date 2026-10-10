# FinOps / Cost Engineering — 配賦した cent はどこへ行った？

この有限1教材は、**架空の固定 ratecard / usage** を使う cent 配賦の計算模型。市場価格ではない。通貨 `XCU` も架空で、1 XCU = 100 cents と定義する。実クラウド価格API、billing API、税、実財務助言、契約/購入/実課金は行わない。17条件の計算をこのMacの既存Python標準ライブラリで実行する。Subject全体・Atlas全分野の完成を意味しない。

[学習UI](index.html)で **予想→操作→保存計算の比較→原典/実装→答え** を辿る。ブラウザの比較操作は保存原票の表示であり、請求操作や計算の再実行ではない。

## 前提 → 主要概念 / 仕組み

整数の足し算、割り算の余り、単価×数量を知っていれば始められる。

1. **source charge**：usageの `quantity × ratecard[sku]` をDecimalで計算し、各usage行と共有費用sourceを個別に `ROUND_HALF_UP` でcentへ丸める。本模型のルールで、実providerの請求丸めとは限らない。例えば3×0.105 XCU = 0.315 XCU →32 cents、0.5×0.21 =0.105→11 cents。32+11=43 cents。全exact値を先にまとめてから丸める方式は今回のsource chargeルールではない。
2. **direct attribution**：A/B/C tagを持つusageはそのteamへ直接配賦。tag欠落は `unallocated.direct_cents` に残す。欠落費用を黙って除外しない。共有費用のbasis（weight）は別の明示入力で、direct usageから自動推測しない。
3. **fixed shared resource**：固定のshared_amountをcentへ丸め、そのinteger centをweight比で分ける。10 centsをA/B/Cに等分すると、それぞれ正確には10/3 cents。3件を個別roundすると3+3+3=9で1 cent不足する。11 centsなら4+4+4=12で1 cent過剰になる。
4. **総額保存**：各shareのfloorを取る → source cent−floor合計の残りを算出 → 小数余りの降順、同率はteam IDの辞書順昇順（A→B→C）で1 centずつ配る。10 centsはA4/B3/C3、11 centsはA4/B4/C3。入力mapやusageの順序を反転しても配分先は変えない。これは本教材の固定規則で、FinOps Foundationがこの丸め算法を義務付けているという意味ではない。
5. **basisなし**：weight mapが空なら共有全額を `unallocated.shared_cents` へ置く。weight0を空mapと同一視せず、無効入力として拒否。unallocatedは会計上の差額埋めではなく「配賦先/根拠が未決の費用」。丸め差額は別の `rounding_gap_cents = source_total − 全leaf合計` として表示する。

[FinOps Foundation Allocation / Definition](https://www.finops.org/framework/capabilities/allocation/)から、allocation/tagging/shared costの戦略を分けるという接点を読む。本教材のratecardと配賦方針は架空で、実組織の承認済み戦略ではない。

### Decimal context と数値の契約

`localcontext(Context(prec=28, rounding=ROUND_HALF_UP, Emin=-999999, Emax=999999))` を固定し、`FloatOperation` trapを有効にする。accepted rate/quantity/shared_amount は最大6桁整数部・最大6桁小数部のdecimal文字列のみ、usage最大8行、weightはA/B/Cの整数1..1000。quantityは正、rate/sharedは0以上。binary floatをDecimalへ渡したりfloatを経由して計算しない。JSON数値0.1は意図した無効inputとしてのみ登場し、計算へ入る前に拒否する。

Decimalの循環share（10/3など）のraw表示はprecision28の近似であり、数学的にexactな有限小数ではない。checkerは `Fraction` でexact rationalを作り、integerのfloor・余り順位・HALF_UPとliteral hand-cent期待値で独立検算する。受入済み小入力の結果を確認しているので、任意精度/巨大入力の配賦保証には広げない。[Python3.9 Decimal / Context, Rounding modes, FloatOperation](https://docs.python.org/3.9/library/decimal.html)が原典。

## 今回実装 / 正常・境界・意図異常

下表は独立手計算の期待値。実計算原票は [pointer](observation-data.js)・UIから辿る。異常を予想通り検出したことと費用の保存を分ける。

| 条件 | source / 全leaf cent | A/B/Cのtotal cent | unallocated direct/shared | gap / 判断 |
|---|---|---|---|---|
| normal-weighted | 52 / 52 | 24 / 28 / 0 | 0 / 0 | 0、共有12を1:2へ4/8 |
| equal-conserved | 100 / 100 | 24 / 33 / 43 | 0 / 0 | 0、共有10を4/3/3 |
| equal-naive | 100 / 99 | 23 / 33 / 43 | 0 / 0 | +1、個別roundで不足 |
| round-up-conserved | 11 / 11 | 4 / 4 / 3 | 0 / 0 | 0、共有のみ |
| round-up-naive | 11 / 12 | 4 / 4 / 4 | 0 / 0 | −1、個別roundで過配賦 |
| tie-reordered | 100 / 100 | 24 / 33 / 43 | 0 / 0 | 0、map/行逆順でもtieはA優先 |
| missing-tag | 60 / 60 | 25 / 5 / 0 | 30 / 0 | 0、tag欠落費用を保持 |
| no-basis | 30 / 30 | 20 / 0 / 0 | 0 / 10 | 0、basisなし共有は未配賦 |
| one-cent | 1 / 1 | 1 / 0 / 0 | 0 / 0 | 0、1 centだけAへ |
| fractional-usage | 53 / 53 | 40 / 13 / 0 | 0 / 0 | 0、direct32/11、共有8/2 |
| zero-shared | 40 / 40 | 20 / 20 / 0 | 0 / 0 | 0、共有0は有効 |
| zero-quantity / negative-quantity | 計算拒否 | cost treeなし | cost treeなし | quantity≤0は無効 |
| float-quantity / nonfinite-rate | 計算拒否 | cost treeなし | cost treeなし | decimal文字列契約違反 |
| duplicate-usage / zero-weight | 計算拒否 | cost treeなし | cost treeなし | 二重source charge/無効basisを防ぐ |

全inputのvalidate後にcostを作るので、拒否条件は部分的なsource/配賦を残さない。naiveのgapをunallocatedへ押し込まない。missing-tag/no-basisはgap0でも未配賦が残る。総額一致だけで「全費用のownerが確定」「公平なweight」とは判断できない。

### このMacで再現

Python3.9以降の既存stdlibのみ、Docker/外部service/new dependency/global installなし。

```sh
# このREADMEのあるディレクトリで実行
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
PYTHONDONTWRITEBYTECODE=1 python3 quick_validate.py
# 明示更新: 新原票を作り、oracle一致時だけUI pointer更新
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record
# 表示された動的portをIABで開く。owned serverはCtrl-Cで終了
python3 -u -m http.server 0 --bind 127.0.0.1
```

[calculator](calculator.py)・[runner](runner.py)・[独立read-only checker](checker.py)・[公式locator/binding](sources.json)・[教材限定Skill](skills/atlas-finops-cost-engineering/SKILL.md)。通常checkerはJSONを読むだけ。runner無optionは書かず終了。`--record` だけが新runを作り、旧runを消さず成功時にpointer更新する。

`run.json` に実UTC時刻・Python/OS/architecture・source digest、case別 `input.json` に架空ratecard/usage/shared/weight/policy、`result.json` にraw各段階/context/cost tree、`oracle-report.json` と `oracle-command.json` にFraction/手計算照合、`artifact-index.json` にinput/raw/result/artifact digestを保存。index自体は自己参照を避け分母外。source内容と原票をhashでbindingするが、hashは業務上の公平性を証明しない。

## 実務判断

今回から判断できること：丸める単位（sourceかleafか）を先に決めないと、同じweightでも費用を生み消しする。余り配分先・順序を明示すると再現できるが、team Aに余りが集まる偏りを受け入れるかは別の方針判断。tag不明/basisなしを明示することで、総額の照合とowner coverageを別々に評価できる。costをinteger minor unitへ正規化しても、billing行の重複、通貨、期間、訂正を扱わなければ実請求との一致は分からない。

模型の総額保存条件は、source charge整数centが確定し、同じcurrency/unitの値を使い、妥当なpositive weightsで全shareを処理し、direct/unallocatedを含む全leafを数えること。naive版は意図的にこの保証を満たさない。正しい配賦は削減額・予測精度・経営上の価値を意味しない。

## 限界 / Subject主要未教材coverage / 次の実験

この有限教材から次に学ぶべき主要領域を4実験へ対応させる。いずれも提案・未実行で、自動開始しない。

| 次の実験 | 主要概念 / 問い | 小さいinputと比較する観測 | 公式locator |
|---|---|---|---|
| E1: cost dataの意味と照合 | ingestion、schema/lineage、billed/effective/list cost、billing/charge期間、currency、credit/refund/correction、allocation metadata、granularity。請求行と配賦の分母は一致する？ | 架空FOCUS風20行を生成し、duplicate/訂正/欠落tag/異通貨を入れる。source lineage別総額、invoice別比較、numeric/unit/complete条件を検査。実billing importは別途明示scopeでのみ | [FOCUS1.4 / §2.7 Attribution, §2.10 Split Allocation, §4.13 Numeric Format, §8.14 Rounding Variance Tolerance](https://focus.finops.org/docs/specification/v1-4/)・[Allocation / Inputs & Outputs](https://www.finops.org/framework/capabilities/allocation/) |
| E2: unit economicsと予算/予測 | business denominator、cost per request/tenant/job、forecasting、budget、anomaly、seasonality/uncertainty。costが下がったのは効率化か単に処理量低下か？ | 架空12期間のusage/成功request/費用を用い、volume/rate/mixの変化を分解。予測とholdout誤差、total costとunit cost、失敗requestの扱い、tag coverageを比較 | [Unit Economics / Definition, Functional Activities](https://www.finops.org/framework/capabilities/unit-economics/)・[Forecasting / Measures of Success](https://www.finops.org/framework/capabilities/forecasting/) |
| E3: 最適化とtradeoff | rightsizing、idle/scheduling、storage lifecycle、network/egress、container/shared capacity、commitment/reservation/spot、rateとusage、performance/SLO。節約がSLOや利用率を壊さないか？ | 架空capacity4/8と負荷trace、価格係数・commitment使用量を固定し、cost/SLO miss/idle/coverageを比較。実価格や契約購入は行わず、未利用commitmentと削減仮定を明示 | [Usage Optimization / Definition, Functional Activities](https://www.finops.org/framework/capabilities/usage-optimization/)・[Rate Optimization / Functional Activities](https://www.finops.org/framework/capabilities/rate-optimization/) |
| E4: owner policyと運用 | showback/chargeback、tag taxonomy、shared basis変更、allocation drift、governance、reconciliation/approval、cost visibility/access、KPI。owner/weight変更をどの期間から適用する？ | 2期間×3teamsの架空policyを版管理し、retroactive weight/tag変更前後を比較。source保存、unallocated率、未承認policyのhold、再計算lineage、owner別表示を検査 | [Allocation / strategy, tagging, shared cost, Validate allocation compliance](https://www.finops.org/framework/capabilities/allocation/)・[FOCUS / cost attribution, dataset completeness, invoice reconciliation](https://focus.finops.org/docs/specification/v1-4/) |

実provider価格、tier/discount/commitment購入、税/FX、real invoice、billing ingestion、実resource操作、実財務判断は今回未実行。模型は1架空currency・cent・3teams・小inputで、任意malformed inputのproduction validatorでもない。FOCUS exportや仕様準拠を主張しない。

## 原典 → 答え

[source locator一覧](sources.json)の `binding/status` で、公式資料と今回の模型/次実験の接点を確認する。FOCUSのoverviewは取得時にpublished1.4へredirectしたのでversionをlocatorへ固定。ここに規格準拠や実課金検証の証拠を作らない。

今回の答え：**source centを決め、共有weightと余り規則を明示し、unallocatedと丸めgapを分けて全cost treeを足す。** [実IAB QA/capture/owned cleanup](qa/README.md)は計算原票と別の証拠。Core/Graph/Portal/harness、commit/push/公開、Goalは今回対象外。
