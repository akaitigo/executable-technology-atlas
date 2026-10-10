# Argo CD：PruneLastは、どのwaveを上書きする？

[前単元「prune順序」](../argocd-prune-order/README.md)に続き、通常の逆waveとPruneLast指定後の計画を比較します。全体指定、資源単位指定、全waveが負、PreSyncが大きいwaveを持つ場合を、固定5ケースで手計算してからPython模型で照合しました。

入口は[操作reader](index.html)とCLIです。候補waveと対象資源を予想し、元wave→通常逆wave→指定後を3段階で対照できます。1280px/390pxの実GUI操作と7枚の実capture目視を確認しました。**LIVE Argo CD・Kubernetes・Docker・Goコードの実行はしていません。Healthや削除完了も未観測です。** 準備済みタスク集合を固定し、waveOverrideを説明する模型です。[GUI検証記録](GUI-QA.md)も参照してください。

## 分野ゴールとの対応

既存 `atlas-97-field-goals-ja.md` 第62項「Argo CD」のprune判断と、前単元COVERAGEのPruneLast未対応を引き継ぐ次課題です。前単元の原票・UI・受入記録を修正するものではありません。

|到達目標|今回の到達点|
|---|---|
|説明する|通常の逆waveと、PruneLastによる後の上書きを区別する。|
|操作する|5ケースをCLIで選び、上書き候補と対象資源を予想して照合する。|
|検証する|実装前の手計算と、固定版の最大値計算・対象判定を対応づける。|
|実務で判断する|全体指定か資源単位指定か、指定していないpruneが残るかを確認する。|
|前提を使う|Desired/Live、Sync phase、wave、通常pruneの対称交換を使う。|
|未対応を分ける|計画への配置と、Healthを含む実行条件・削除完了を別に読む。|

## 1. 先に予想する

全タスクがSyncの基本例です。全体PruneLastを無効にした通常計画と、有効にした計画を比べます。

|資源ID|処理|元wave|
|---|---|---:|
|app-a|apply|0|
|app-b|apply|5|
|old-low|prune|−3|
|old-high|prune|8|

まず次の3点を予想してください。

- PruneLastの上書き先はapply最大waveの5に1を加えた6か、それとも別の値か。
- old-lowだけ資源単位指定したとき、old-highも後ろへ動くか。
- 全waveが負の場合や、PreSyncにwave 20がある場合、上書き先はどう決まるか。

資源単位の `prune_last` は、live側の指定を判定済みとする教材入力です。annotation文字列を解析した実測ではありません。

## 2. 操作して対照する

画面では [index.html](index.html) をfile://で開き、ケース・候補wave・対象資源を予想します。「次の段階へ」を3回進め、原典を読んでから答えを開いてください。予想変更では段階と答え、resetとケース変更では予想も初期化します。入力エラーは予想の書式の問題であり、Argo CDの同期失敗を示しません。通信やサーバー起動は不要です。

このディレクトリで実行します。Python標準ライブラリだけを使い、外部通信・書込みはしません。

```sh
# 入力を見て予想する
python3 -B model.py --case global --view input

# 上書き先と対象資源を予想して答えと比べる
python3 -B model.py --case global --predict-wave 9 --predict-selected old-high,old-low

# 指定なし／資源単位指定／負wave／phaseの境界へ進む
python3 -B model.py --case ordinary
python3 -B model.py --case resource-only
python3 -B model.py --case all-negative
python3 -B model.py --case presync-excluded
```

`--json` で元の比較結果と予想の正誤を取得できます。CLIは[fixtures.json](fixtures.json)の5ケースを選ぶ入口です。任意のmanifestをclusterへ適用する機能ではありません。

出力は「元wave → 通常の逆wave後 → PruneLast指定後」を並べます。planの `{old-high, old-low}` は同じphase/waveの資源集合です。左に書いた資源が先に完了する、という意味ではありません。

## 3. 原典と実装を確認する

対象はArgo CD v3.5.2、commit `e258ee23c3e52266d407572f4bcdfe7d9ed36cb5`。前単元で正式取得した固定版の表示本文を再利用し、追加の取得は行っていません。

|固定版の箇所|計画へ取り込んだ処理|
|---|---|
|[sync_context.go 1014–1041行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L1014)|prune waveの対称交換が先。|
|[1042–1052行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L1042)|最大値探索は0から始め、Syncの有効waveを調べて1を加える。pruneも含む。|
|[1053–1058行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L1053)|pruneであり、全体指定または資源単位指定があるtaskのwaveOverrideだけを設定する。|
|[1060行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L1060)|この後にSort。今回はNamespace/CRD調整がない入力へ限定する。|

phaseを上書きする処理ではありません。phase優先の比較は、既存の[依存順序単元の原典記録](../argocd-dependency-order/source-review.json)も参照しています。

[source-review.json](source-review.json)に再利用した取得記録と未検証範囲を残しています。raw byte列の保存・SHA-256取得はしていません。Goの実装をビルド・実行した証拠でもありません。[model.py](model.py)は、この有限条件の計画だけを実装したPython模型です。

## 4. 答え合わせ

[hand-oracle.json](hand-oracle.json)と[固定時点の記録](hand-oracle-lock.json)を模型・validatorより先に保存しました。

|ケース|通常逆wave後のSync最大値（初期値0）|PruneLast候補|上書き対象|指定後の計画|
|---|---:|---:|---|---|
|ordinary|8|9|なし|old-high/−3 → app-a/0 → app-b/5 → old-low/8|
|global|8|9|old-high、old-low|app-a/0 → app-b/5 → {old-high, old-low}/9|
|resource-only|8|9|old-lowだけ|old-high/−3 → app-a/0 → app-b/5 → old-low/9|
|all-negative|0|1|old-high、old-low|app/−4 → {old-high, old-low}/1|
|presync-excluded|0|1|oldだけ|PreSync pre-check/20 → Sync app/0 → Sync old/1|

基本例の通常逆wave後はold-lowが8、old-highが−3です。最大値探索にはpruneの8も入るため、候補は6ではなく9です。指定なしでは候補9を計算しても使いません。

全waveが負の例は、通常計画がold-high/−7、app/−4、old-low/−2。探索の初期値0が残るので候補は1であり、−1ではありません。

最後の例はPreSyncのwave 20をSync最大値へ含めません。PruneLastでoldのwaveを1へ変えても、phaseはSyncのままです。PreSyncは数値20でもSyncより前のphaseとして配置します。hookの成功やHealthを観測したという意味ではありません。

## 5. 検証結果と実務判断

```sh
python3 -B verify.py
```

通常検査は書込みなし。初回保存用の `--record` は既存原票の上書きを拒否します。

手計算5ケース・18タスク入力が一致し、想定外入力の拒否10件、出力改変検出5件、CLI5件も初回passしました。模型検査0.001089秒、CLI込み0.261692秒。性能測定ではありません。[実行原票](observations/model-check.json)に実行時hash、各ケースの結果、CLIの出力を保存しています。

出力改変検出は、pruneを最大値から外す、資源単位指定を全体へ広げる、初期値0を無視する、PreSyncを混ぜる、phaseまで変える、という誤りを弾く確認です。upstreamへのmutation testとは区別します。

実務ではまず指定の範囲を確認します。old-lowだけの指定から、すべてのpruneが後ろへ動くと判断しないでください。同waveへ集まった資源の依存が、名前の並び順で安全になるという保証もありません。

**後ろへ配置した計画と、そのwaveへ実際に到達する条件は別です。** この模型にはHealth状態がなく、「全資源がHealthyになるまでの動作を検証した」とは言えません。待機・失敗・hook・retryの影響や実資源の消滅は、controllerの実行経路と観測を使う別の検証が必要です。

## 6. 限界と未対応

入力は準備済みの固定task集合です。pruneはSyncに限定し、phaseはPreSync/Syncだけ。Namespace/CRD依存調整、task再生成、annotationパーサー、pruneObject/API結果、権限、削除保護、確認、propagation、finalizer、cycle解消、一般schedulerを実装していません。

readerの自GUI/画像QAを完了しました。独立受入は別reviewerの記録に従い、LIVE実験は未実施です。次の不足は削除確認・削除保護、Healthを含む到達条件の切り分けです。[次の単元案](NEXT.md)、[COVERAGE.md](COVERAGE.md)、[Skill](SKILL.md)、[制作状態](observations/status.json)に対応を記録しています。

旧教材・統合repo・共有台帳・全体受入カウントは変更せず、この独立ディレクトリにだけ保存しました。分野全体の完成や公開を宣言するものではありません。
