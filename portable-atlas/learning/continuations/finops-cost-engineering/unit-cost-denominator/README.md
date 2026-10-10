# unit cost：成功requestを分母にする

[元Subject FinOps / cent配賦](../../../subjects/finops-cost-engineering/README.md) README E2の有限部分です。E2の12期間・volume/rate/mix分解・forecast/holdout・季節性は未実装。ここでは架空2closed batchの費用/件数と成功分母の比較だけを実装しました。Subject/Atlas全体の完成ではありません。

前提は整数cent、件数、分数、比率。読む順番は元Subjectでsource cent/配賦済費用と総額保存→本教材で費用範囲と業務分母→[capacity投入/受理/完了/drop](../../performance-capacity-engineering/two-server-bounded-queue/README.md)でcohortを確認。本教材の「成功」は事前入力の業務成功件数、capacityのfinishと同一とは限りません。capacityのruntimeを呼び出して成功数を作りません。UIは総額/分母/unit予想→条件操作→表/比率比較→原典/実装/raw→答えです。

## 独自費用範囲と先固定の手計算

通貨XCUは架空で1 XCU=100cent。費用範囲はcompute＋配賦済sharedの2整数cent行のみ。source費用は既に固定済みで、本教材では配賦/丸め/rate×usageを再実行しません。市場価格、provider bill、組織の承認済みcost定義ではありません。失敗attemptの処理費用もsource総額に含まれているという独自契約です。税、FX、返金、人件費、収益、TCOは含みません。費用は固定入力なのでattempt数と線形に連動せず、attempt0でも費用を持てます。

baseline/candidateは架空の閉じたbatch、attempt/successは同じbatchに属する事前集計値。成功は業務成功requestとして固定し、retryや一意request IDから集計した実測ではありません。件数0..1000、cent0..100000、型はJSON整数のみ、boolを除外。success≤attempts。同XCUのcost行2本だけを受理します。負件数、success>attempt、異通貨、bool、float等の固定10拒否例を計算前に拒否し、部分総額を残しません。任意malformed inputのproduction validatorではありません。

| case | baseline / candidate総cent | attempts | success | candidate使用分母 | candidate unit cost | 総額比 / unit比 | 判断 |
|---|---|---|---|---|---|---|---|
| lower-total-higher-unit | 100 / 60 | 100 / 100 | 100 / 30 | 30成功 | 2 | 3/5 / 2 | 総額40%減、unit倍 |
| same-unit | 100 / 60 | 100 / 100 | 100 / 60 | 60成功 | 1 | 3/5 / 1 | unit不変 |
| zero-success | 100 / 20 | 100 / 10 | 100 / 0 | 0成功 | undefined | 1/5 / undefined | 成功単位未定義 |
| zero-attempt | 100 / 20 | 100 / 0 | 100 / 0 | 0成功 | undefined | 1/5 / undefined | idle費用あり |
| zero-cost | 100 / 0 | 100 / 100 | 100 / 30 | 30成功 | 0 | 0 / 0 | unit0は定義済 |
| zero-baseline-cost | 0 / 60 | 100 / 100 | 100 / 30 | 30成功 | 2 | undefined / undefined | baseline unit0、相対比未定義 |
| bad-all-attempts | 100 / 60 | 100 / 100 | 100 / 30 | 誤って100attempt | 3/5 | 3/5 / 3/5 | 成功あたり改善と故障受入 |

baseline通常unit=100/100=1。総額比はcandidate/baseline、相対変化は比−1。正しい候補は60/30=2、unit比2、相対変化+1（100%増）。総額比60/100=3/5、変化−2/5（40%減）。故障版は60/100=3/5=0.6 cent/attemptを「cent/成功request」と誤表示し、改善を誤受入。attemptあたりという別metricとしての3/5は計算可能ですが、成功あたりと同じ評価にはできません。

成功0のunitはnull/undefinedで、Infinity、0、100%へ置換しません。baseline費用0は両batchのunitが定義済みでも相対比の基準が0です。unitそのものの未定義と比較比率の未定義、契約拒否、実行失敗を別に示します。

hand-oracle.jsonの費用/attempt/success/分母/Fraction期待値はproducer採取前に固定。producerの算術はfractions.Fractionで、jsonへ分子・分母・exact文字列として出力し、float/Decimalへ変換せず丸めません。環境/配信/記録は既存Python stdlibのみ。oracle.pyはproducerをimportせず、独立の整数pairとEuclid簡約・cross-productから総額/分母/ratioを導出し手計算表と照合します。比率の数値だけでなく使用分母の意味を検査します。

## 実行・原票・検査

このdirectoryで `python3 -B runner.py --case lower-total-higher-unit`。fresh保存は明示的 `python3 -B runner.py --record` のみ。採用原票はobservations/20261005T135136267491Z/raw.json、record command exit0。UTC/Python/OS/machine、入力、cost行/総額/attempt/success/失敗/使用分母/exact比、calculate/runner/fixture/先固定表SHAを保存。

`python3 -B check.py` は保存原票の独立整数oracle/固定表を照合。総額、件数、使用分母、分数cross-product、total ratio/change、unit ratio/change、故障判断、10拒否を分けます。6意味ある改変を拒否。通常checkerとSkill routeは全ファイルSHA/mtime不変で、保存しません。

`python3 -B server.py` は専有127.0.0.1:0のUIから同Fraction処理を実行。case変更は3予想unknown、各予想単独変更は新しい選択を保持して比較/表/trace/raw/答えを消します。全run-startで共通clearし、generationで旧応答を破棄。EXECUTION_FAILUREはphase/error/未確認で旧正常答えを残しません。INPUT_REJECTEDと成功0は実行障害ではありません。

observations/ui-qa/preview.pyはQA専用の返却失敗/HTTP503/保留応答注入です。実billing障害や実料金操作を再現したとは主張しません。実IAB captureは表示のみならローカル未保存と記録し、再構成画像を作りません。sandbox bind拒否を残して同serverをhost許可で起動。所有tab/portだけ片付けます。

## 原典と実務判断・限界

一次資料[FinOps Foundation Unit Economics](https://www.finops.org/framework/capabilities/unit-economics/)のDefinition、Functional Activities（FinOps Practitioner / Product / Finance）を2026-10-05確認。業務metric、仮定、費用に含める範囲とunit定義を明記し、総額と業務成果を関連づける観点へ接続します。原典が成功request分母や本架空costを必須としているとは主張しません。文章/図/コードは転載していません。

総費用40%減だけでは業務効率改善とは判断できず、件数・成功定義・費用範囲の一致を別に確認します。結果は架空固定cent/2batchの算術のみ。実billing/real価格、forecast、予測誤差、季節性、volume/rate/mixの因果分解、施策の因果改善、金融判断、収益/ROI、実利用者価値は未実証。設定/依存install/課金/公開/commit/push、Core/fullGateは未実施。

## 次の未実施案

1. retry/一意request IDとcapacityのoffered/admitted/finished/dropを対応づけ、成功分母のlineageを検査する。現在は事前固定countのみ。DefinitionとProductのunit定義へ接続。
2. E2の架空12期間でforecast/holdoutとtotal/unitの誤差を分ける。現在は予測/季節性なし。実価格や因果改善へ広げない。
3. 費用scopeの版とshared込み/除外を比較し、同じmetric名の比較可能性を検査する。現在は2行固定scopeのみ。Functional Activitiesの仮定/費用範囲へ接続。
