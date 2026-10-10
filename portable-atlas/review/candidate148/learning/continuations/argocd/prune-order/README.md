# Argo CD：作る順序と、消す順序は同じ？

これは[前単元「Namespace／CRDの依存順序」](../argocd-dependency-order/README.md)に続く**新しい課題**です。前単元で未対応としたlive-only資源のpruneについて、通常applyとのwave順の違い、削除待ち、失敗時の後続境界を5つの有限例で比べます。

入口は[操作reader](index.html)とPythonの学習CLIです。readerは検証済み原票を段階表示します。1280px・390pxの実GUI操作と6枚の実capture目視を確認しました。**LIVE Argo CD・Kubernetes・Docker・Goコンパイラーは実行していません。** 結果コードとlive観測を仮定として与える説明模型であり、削除APIやcontrollerの実測ではありません。[GUIの検証記録](GUI-QA.md)に範囲を残しています。

## 分野ゴールとの対応

既存の `atlas-97-field-goals-ja.md` 第62項「Argo CD」のprune判断を進めます。既存のreconciliation-drift教材はpruneの有効・無効、同期Labは通常applyのwave失敗を扱っています。本単元は、それらと重なる導入を増やさず、逆waveと待機・失敗の境界に絞っています。

|到達目標|この単元でできること|
|---|---|
|説明する|元waveと、prune用に変更した有効waveを区別する。|
|操作する|ケースを選び、開始順と停止の予想をCLIで照合する。|
|検証する|模型実装前の手計算5ケースと、固定版の処理箇所を対応づける。|
|実務で判断する|Prunedという結果と、live資源の消滅観測を分けて読む。|
|前提を使う|Desired/Live、tracked資源、phase/wave、前単元の依存調整との関係を確認する。|
|次へ進む|PruneLast・削除確認・削除保護の条件を別課題として切り分ける。|

## 1. 予想する

同じSync phaseの3つのConfigMapを考えます。名前をlow、mid、highとし、それぞれの元waveを−3、1、8に固定します。apply側ではtargetがあり、prune側ではtargetなし・liveありのtracked資源として、すでにタスクが作られたところから始めます。

比較に使うタスク集合と有効waveは、この初期計画に固定します。途中のlive観測を与えて停止境界を読む一方、controllerがタスクを再生成する全ループは実装しません。実環境で資源消滅によってタスク集合が変われば、有効waveを再計算する条件も変わり得ます。表の数値が実際の各reconciliationでも保たれる、という記録ではありません。

|資源|low|mid|high|
|---|---:|---:|---:|
|元wave|−3|1|8|
|通常applyの開始順の予想|？|？|？|
|prune用の有効waveの予想|？|？|？|

次の3点を予想してから、答えを開いてください。

- pruneの有効waveは単純に元waveの符号を反転すればよいか。
- highがPrunedになっても、liveにdeletionTimestampが残っているとき、次のwaveへ進むか。
- 同じwaveにoldのpruneとnewのapplyがあり、oldがSyncFailedなら、newは開始するか。

## 2. 操作して対照する

ブラウザで[操作reader](index.html)を開き、場面・開始順の予想・終端の予想を選びます。「次の段階へ」で初期計画、資源の結果、停止境界の順に進め、原典を読んでから答えを開いてください。予想変更では段階・結果・答えを初期化し、場面変更とresetでは予想も消します。file://で動き、サーバーや通信は不要です。

このディレクトリで実行します。Python標準ライブラリだけを使い、外部通信や書込みはありません。

```sh
# 入力だけを見て予想する
python3 -B model.py --case prune-descending --view input

# 予想した開始順と終端を照合する
python3 -B model.py --case prune-descending --predict high,mid,low --expect-stop consumed

# apply側と比べる
python3 -B model.py --case apply-ascending

# 削除待ちと、同waveの失敗境界を読む
python3 -B model.py --case prune-waiting --predict high --expect-stop wait
python3 -B model.py --case mixed-same-wave-failed --predict old --expect-stop failed
```

`--expect-stop` は `consumed`（用意した計画を消費）、`wait`（次のreconciliationで削除待ち）、`failed`（現在のprune処理から失敗を返す）の3つです。`--json` で全結果を読めます。CLIは[fixtures.json](fixtures.json)の5ケースを選ぶ入口で、任意のmanifestをclusterへ適用する道具ではありません。

入力にあるresultとobservationは、教材作者が置いた仮定です。未着手タスクの欄は「開始したなら与える予定の仮定」であり、観測済みとは扱いません。模型出力の `results` には開始した資源だけを残します。

|観測値|この模型での意味|
|---|---|
|`ready`|非最終applyの後、次waveへ進める状態を別に与えた。Healthyの計測ではなく、Health判定なしで成功する経路もまとめた前提。|
|`absent`|次の境界でlive資源がない、と別に与えた。Prunedから自動推定していない。|
|`terminating`|Pruned・liveあり・deletionTimestampあり、を次のreconciliationの観測として与えた。|
|`unobserved`|それ以後のlive/Health状態を与えていない。失敗理由や最終資源の消滅を推測しない。|

## 3. 原典と実装を確認する

対象はArgo CD v3.5.2、commit `e258ee23c3e52266d407572f4bcdfe7d9ed36cb5`。以下は固定した[公式sync_context.go](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go)の処理に対応します。

|確認箇所|模型へ取り込んだ境界|
|---|---|
|[1014–1041行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L1014)|存在するprune waveを整列し、両端を入れ替える。applyのwaveはこの交換対象ではない。|
|[558–568行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L558)|Prunedのliveが削除中なら、次のreconciliationは削除待ちで戻る。|
|[612–621行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L612)|現在のphase/waveを選んでrunTasksへ渡す。|
|[1493–1523行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L1493)|その組の中でpruneを先に処理し、SyncFailedなら後のapplyへ進まず戻る。|
|[1560–1574行](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_context.go#L1560)|prune段階を通った後にapply側を処理する。|

「pruneが先」は現在のphase/wave内の話です。全waveのpruneをすべて終えてから全applyを始める、という意味には広げません。同waveで複数pruneがある実装の並行処理も、この模型の1資源ずつの表から完了順を推測できません。

[source-review.json](source-review.json)に取得経路と未読範囲を残しています。正式text取得は1tool呼出・同一URLの3表示窓で成功しました。raw byte列の保存とSHA-256取得はしていません。`pruneObject`の全分岐や削除API結果を自動照合した検査でもありません。[model.py](model.py)はこの限定処理を説明するPython実装です。

## 4. 答え合わせ

[hand-oracle.json](hand-oracle.json)と[固定時点の記録](hand-oracle-lock.json)は、模型・validatorより先に保存しました。元waveは−3、1、8。対称交換後はそれぞれ8、1、−3です。**−waveの3、−1、−8ではありません。** 有効waveを昇順で処理すると、元waveが大きい資源から消す計画になります。

|ケース|計画・開始した資源|模型が終わる箇所|未着手|
|---|---|---|---|
|`apply-ascending`|low → mid → high|最後のapply結果まで入力した。最終Healthは未観測。|なし|
|`prune-descending`|high → mid → low|最後のPruned結果まで入力した。lowの消滅は未観測。|なし|
|`prune-waiting`|highだけ|次のreconciliationでhighの削除待ち。|mid、low|
|`prune-failed`|high → mid|midの結果がSyncFailed。|low|
|`mixed-same-wave-failed`|oldだけ|wave 0のpruneから失敗を返す。|同waveのnew、wave 2のlater|

最初の2例の `plan-consumed` は、用意した計画を消費したという**教材独自の終端名**です。Argo CDのOperationPhaseを全面再現した値ではありません。Prunedという資源結果とlive資源が消えた事実は別です。最終waveでも必ず消滅まで待つ、という一般化はこの教材では行いません。

削除待ちの例は後続waveを持つ場面に限定しました。同じwave内のapplyまで削除完了待ちになる、と教える例ではありません。失敗例も、SyncFail hook・retry・他の実行中タスクの処理へ広げず、`runTasks`が失敗を返す境界で終えます。

## 5. 検証結果と実務判断

```sh
python3 -B verify.py
```

通常検査は保存原票を書き換えません。初回保存用の `--record` は既存原票の上書きを拒否します。

実行済みの検査は、手計算5ケース・15タスク入力、想定外入力の拒否12件、出力の改変検出5件、CLI4件です。初回pass、retry 0。模型検査は0.001112秒、CLI込み0.204976秒でした。[実行原票](observations/model-check.json)に実行時のファイルhashと結果を保存しています。これは軽い模型検査の時間であり、Argo CDの性能値ではありません。改変検出は「誤った出力をoracleとの比較が弾く」検査で、upstreamへのmutation testではありません。

追加で[CLIの対照表示1件](observations/cli-reader-check.json)を実行し、同waveの未着手資源と誤った予想への応答を確認しました。文書は模型検査後に整えています。実行時原票のhashは保持し、[文書確認の記録](observations/document-review.json)を別にしています。

pruneの後続が始まらないときは、まず元waveと有効wave、資源結果、liveの有無とdeletionTimestampを別々に確認します。SyncFailedなら、その理由を実際のcontroller/APIの記録で確認する必要があります。この模型の仮定から権限不足やfinalizerなどの原因を断定しません。waveの変更だけで、削除の許可や安全な依存解消が保証されるわけでもありません。

## 6. 限界と次の未対応課題

条件はSync phase、ConfigMap、prune有効、dry-run無効、PruneLast無効、確認条件充足、hookなし、Namespace/CRD調整なし。各有効waveでprune/applyはそれぞれ最大1資源です。タスク生成、tracked/orphan分類、APIの応答生成、全Health処理、実時間、一般scheduler、cycle解消は実装していません。

次は**PruneLast・削除確認・削除保護の組合せ**です。今回読んだ固定版にはPruneLastの別wave上書きがありますが、それを通常の逆waveと同じ規則として扱わず、確認できた範囲を分けて追加する必要があります。propagation policy、finalizer、最終wave後の消滅確認、実clusterでの追試も未対応です。

本単元の制作・模型検証・readerの自GUI/画像QAを完了しました。独立受入は別reviewerの記録に従います。LIVE QA、統合、公開、分野全体の網羅、受入単元数への加算は行っていません。旧教材・源repo・共有台帳は変更していません。[COVERAGE.md](COVERAGE.md)、[Skill](SKILL.md)、[制作状態](observations/status.json)に範囲を残しています。
