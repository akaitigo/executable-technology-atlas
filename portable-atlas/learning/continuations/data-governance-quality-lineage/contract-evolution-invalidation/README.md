# 品質contractの変更とcache失効・再検査

問いは「sourceが同じなら、contractが変わっても旧cacheを使えるか」です。[元Subject](../../../subjects/data-governance-quality-lineage/README.md)の[coverageの次実験](../../../subjects/data-governance-quality-lineage/coverage.json)を具体化します。関連する[CSV ingest・quarantine教材](../../../subjects/data-engineering-orchestration/README.md)とは、JSON batch全体受理の境界を分けます。元教材→前提→UI予想→bindingと再評価→原典/実装/raw→実務判断の順で読みます。旧教材は再実行・変更していません。

## 前提 → 予想 → 操作

JSON、型、range、SHA256、cache keyを前提にします。合成sourceは1行r1/amount100だけ。初期contractはversion v1、integer-not-bool、0≤amount≤100。初期合計100を信頼済みfixture cacheとして保存します。

1. 単元directoryで `python3 checker.py`。保存原票を独立手書き表と固定byte/hash・合計oracleへ照合。
2. `python3 -m http.server 0 --bind 127.0.0.1 --directory ../../..`。learning rootを読取り配信し、動的portの `/continuations/data-governance-quality-lineage/contract-evolution-invalidation/index.html` を開く。所有serverだけ終了。
3. 条件・予想を選び比較。cache_state→validation_state→violations/amount_sumを読み、答えを開く。条件変更は予想reset。予想変更は新値を保持して旧結果・答えclear、再度比較する。
4. 明示再実測だけ `python3 runner.py --record`。新observationsへ原票を保存し旧run保全。通常runnerは書かずexit1で案内。

## 先に固定した独自契約

重複JSON keyを拒否。parsed JSONをsort_keys、空白なし、ASCIIで正規化しsource/contractのSHA256を作る。producer内容hashもcache keyに含む。標準canonical JSON/CSVW準拠を称しません。versionは完全contractのcache identityには含むが、min/max/typeのvalidation規則を変えないmetadataです。

| 変更 | 正常cache_state | 再評価/結果 | source-only故障版 |
|---|---|---|---|
| なし | reused | cache-reused-accepted / 100 | 再利用100 |
| max100→99 | invalidated | reevaluated-rejected / null、row1 amount最大超過 | 旧受理100を再利用して取り違える |
| version v1→v2だけ | invalidated | reevaluated-accepted / 100 | binding変更を無視して旧受理100 |
| 空白・key順だけ | reused | 正規化hash同じ、100 | 再利用100 |

失効だけでは拒否とは限りません。version変更は失効しても再検査結果が同じ。raw文字列hashが変わってもvalidationの意味が変わったとは断定しません。表記対照ではraw hashだけ変化、version対照では正規化hashも変化するがpredicateは同じです。

5入力（source bool/float、contract bool範囲/上下逆転/重複key）はexpected refusalとしてcache使用前に拒否。source型境界と契約自体の不正をstageで分ける。max99による正当なbatch拒否とは別分類です。

## 原典・実装・rawと独立oracle

[W3C Tabular Data Model](https://www.w3.org/TR/tabular-data-model/) §4.6/4.6.2は型と値制約、§6.6はtable validationを扱います。この独自JSON・cache/version規則は標準から要求された実装ではありません。

engine.pyで実JSON parse/validation/SHA256/cache比較・再評価を実行。binding-check→cache-invalidate→revalidateをtrace保存し、古い結果を破棄した後に新受理/拒否を作ります。source-only対照はsource hashだけで旧結果を返し、contractを照合しない故障です。

expected-table.jsonは実行前の手書き違反表。checker.pyはproducerをimportせず、固定正規化byte literalと別sum([100])からsource/binding/合計を検算し、最大違反位置row1/amount/maximum/value100/limit99を照合。5改変原票検出、command/stdout/exit、source/artifact digestも検査。通常checkerはread-only。UIは保存原票の比較で新validationを実行しません。[QA](qa/README.md)に実IAB/capture/検証証拠。

## 答え → 実務判断

cacheをsourceだけに結び付けると、品質規則が変わった旧受理を持ち出せます。評価に使ったcontract/producerもidentityに含め、失効と再評価を別に記録します。一方、versionや表記差から業務上の意味変更を推定せず、規則差とvalidation結果を見る必要があります。

hashは内容bindingであり、承認・producer真正性・現実のデータ品質や実データ安全を証明しません。専用合成fixtureのみ、署名・外部policy・実service連携なし。

## 次coverage（未実行）

1. null/type/空白ID/重複categoryの違反位置を手書き表へ照合。
2. lineage列edge変更とnonancestor edgeで影響集合と拒否を比較。
3. cache出力とdigest両方の改変で、真正性と意味的検算の境界を比較。

Skillはskills/atlas-contract-evolution-invalidation/SKILL.md。正常6/未対応4routeは構造検査のみ、モデル挙動評価は未実行。標準適合/承認/真正性/実データ安全、Core/fullGate/commit/push/公開は未実行。この有限単元から分野全体・Atlas全体のcompleteを主張しません。
