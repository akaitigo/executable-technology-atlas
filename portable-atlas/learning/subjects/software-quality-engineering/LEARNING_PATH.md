# Software qualityを学ぶ道筋

この文書は[行coverageと境界mutationの既存教材](README.md)から、仕様、入力の選び方、Oracle、失敗の解釈へ進むための補足です。有限教材の補足であり、分野全体の学習完了を示すものではありません。以下の次実験はすべて未実行です。

## 1. 前提と主要概念

整数の半開区間`[lo, hi)`、空区間、真理値、AND/ORを理解します。テストを読む前に、仕様の入力領域と期待値を説明します。ここでは整数-10〜10、lo≤hiという契約があります。

学ぶ順序は **仕様と入力領域 → 期待値Oracle → 例と境界 → coverage → mutation → propertyと縮小 → 統合・非同期 → 運用の品質** です。

- coverageは実行した部分を示します。期待値の妥当性や、誤った実装を区別できることとは別です。
- mutantがkilledとは、変異を有効にしたときテストが違いを検出したことです。survivedには入力不足、弱いassertion、同値など複数の理由があります。
- 同値性は宣言した入力領域で考えます。全JavaScript値に対する同値性と読み替えません。
- Oracleを対象の比較式から複製すると、同じ誤りを正解にしてしまう可能性があります。仕様の別表現や独立した例に戻ります。

## 2. 予想から既存実測へ

[UI](index.html)で境界入力を追加したときの検出数を予想し、[元関数](core.js)、[変異・集合Oracle](experiment.js)、[Node原票](observations/node-20261005-attempt-01/runtime.json)、[実観測記録](VERIFICATION.md)を読みます。この文書作成ではJSやtest runnerを実行していません。

| 実装 | 弱い3入力 | 強い258入力 | 区別する境界 |
|---|---|---|---|
| 元関数 | passed | passed | 仕様と一致 |
| M1 下端を含めない | survived | killed | x=2、[2,5) |
| M2 上端を含める | survived | killed | x=5、[2,5) |
| M3 AND→OR | killed | killed | x=1、[2,5) |
| M4 空区間を受理 | survived | killed | x=2、[2,2) |
| E1 比較を否定形へ | survived | survived | 宣言した整数領域では同値 |

弱いsetは元関数`core.js`の実Node/V8行coverageが100%でも、非同値変異の検出は1/4です。強いsetは弱い3件＋境界3件＋有限集合252件で4/4になります。E1込みの生集計は1/5→4/5で、分母を隠していません。「coverage 100%なら境界誤りを全部検出」という予想への反例です。

異常は元関数の失敗ではなく、故意の変異と仕様の違いです。252件はlo/hi=-3〜3、x=-4〜4の有限列挙であり、乱択生成・shrinking・全入力証明ではありません。UIは同じJS関数を再実行しますが、Node coverageは保存原票の照合表示です。Strykerを動かした結果ではなく、4変異は手作りです。

## 3. 実務で何を判断するか

coverageの低い場所だけでなく、境界、入力拒否、状態遷移、重要な失敗にassertionがあるかを調べます。survivorを減らす際は、必要な仕様差を検出する入力を足し、scoreのために同値例や未実行条件を削除しません。

再現できる失敗入力を保持し、Oracleの根拠、runtime、実装版、seed、test順を記録します。unitのpassからI/O・統合・並行性・性能・security・accessibilityの品質は推論できません。製品の重要なfailure modeと、どの検査がそれを観測するかを対応させます。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [Node v25 Test runner](https://nodejs.org/docs/latest-v25.x/api/test.html)、Collecting code coverage / Timers | 測定対象とcoverageの取得、非同期時間の制御を読む |
| [Stryker Mutant states and metrics](https://stryker-mutator.io/docs/mutation-testing-elements/mutant-states-and-metrics/)、Mutant states / Metrics | killed、survived、timeout、invalid、pendingと分母の違い |
| [fast-check Properties](https://fast-check.dev/docs/core-blocks/properties/)、Introduction / Synchronous properties / Beware of side effects | generatorとpredicate、前提条件、入力非破壊を区別する |

Node公開Docsは取得時v25.9.0で、既存観測v25.2.1とは違います。Stryker・fast-checkは原典の読解だけで、導入・実行していません。既存の同値E1の除外理由とStrykerの一般的なstate分類を混同しません。

## 5. 未教材の問いと次実験

| 未教材 | 問い | 次の入口 |
|---|---|---|
| property生成・shrinking | 大きな失敗入力を小さな反例へ変えられるか | 実験1 |
| 自動mutation・timeout・無効変異 | 実行不能や未実行を分母にどう扱うか | 実験2 |
| 非同期・flaky test | 結果が時刻や順序に依存するとき何を固定するか | 実験3 |
| static analysis・型検査 | 実行前に何を拒否し、runtimeで何が残るか | 別の入力契約・tool検証が必要 |
| regression選択・統合・E2E・fuzzing | unitの外側や未知入力の失敗をどう見つけるか | 別fixtureと観測経路が必要 |
| 性能・security・信頼性・accessibility・CI | 各品質要件をどの条件で測るか | 本教材のscoreでは未評価 |

詳細な既存範囲は[scope.json](scope.json)にあります。

## 6. 次の実験案（3本、すべて未実行）

1. **入力生成と失敗縮小を分けて試す。** 独立fixtureで宣言領域内のlo≤hiとxを、固定seed・有限件数で生成します。集合列挙OracleにM1/M2を照合し、失敗した組から領域と失敗を保ったまま値を小さくする候補を探索します。予想は乱択だけでは境界を逃す場合があり、境界を狙う生成で検出しやすくなることです。生成全入力、最初の失敗、縮小候補、最終反例を保存します。最小性を主張するなら残る有限候補を別列挙で確認し、局所的な縮小だけを全体最小と呼びません。fast-checkのproperty概念を読む入口ですが、独自有限generator/shrinker案で、library実行結果ではありません。

2. **mutation outcomeの分母を独立集計する。** 合成reportにkilled、survived、no coverage、timeout、runtime error、compile error、ignored、pendingを各1件置き、Stryker原典の定義でdetected/valid/totalを手計算した表と照合します。予想は未実行や無効変異をsurvivedとして数える故障版でscoreが変わることです。状態ごとの件数と除外理由を保存し、分母0も独自契約として未定義にします。これはreport集計案です。実timeoutや自動変異生成の証拠は加わらず、実runnerへ広げるなら別processの終了上限と生exit/error記録が必要です。

3. **非同期の順序を固定して同じtestを比べる。** 合成の非同期処理に「結果を更新する」と「assertする」の2eventを置き、完了を待つ正常版と待たない故障版を比較します。仮想timerまたは明示的な完了signalで両順序を再生し、予想は待たないassertionだけがscheduleによってpass/failを変えることです。event順・assert時の値・完了後の値を独立期待表へ照合し、passになる再実行だけを残しません。原典はNode Timersです。固定順の小さなmodelから実OS並行性や全flaky原因へ一般化しません。

## 7. 資料の取得・検証状況

2026-10-05に上表のNode、Stryker、fast-check公式本文を取得しました。先に試したStrykerの`/docs/mutation-testing-elements/mutant-states/`と`/docs/mutation-testing-elements/mutation-testing-metrics/`はInternal Errorで、公式検索結果から上表の統合ページを取得できました。失敗したURLを資料不存在とは判断しません。第三者本文・コードは保存していません。

追加したのはこの文書だけです。runtime、coverage、mutation、checker、UI、global gateは実行せず、既存原票・検証記録・digestを更新していません。次実験の予想は新たな実測証拠ではありません。
