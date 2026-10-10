# Argo CD：Namespace／CRDの依存で、同期の計画はどう変わる？

phase → wave → kind → nameで並べただけでは、最終的なタスク順を説明できない場合があります。Argo CD v3.5.2の `Sort/adjustDeps` を読み、Namespace／CRDの位置と参照が異なる5つの有限例を手で追ってから、軽いPython模型で照合しました。

今回の入口はCLIと対照表です。**LIVE Argo CD、Kubernetes、ブラウザ、画像生成・画像読取は実施していません**。これは同期タスクの並べ替えを説明する模型で、実際の適用成功や資源の作成時刻を測ったものではありません。

## 分野ゴールとの対応

既存の `atlas-97-field-goals-ja.md` 第62項「Argo CD」と、[前のphase／wave教材](../argocd-sync-order/README.md)を引き継ぎます。

|分野の到達目標|この単元で進めること|
|---|---|
|説明できること|入力のphase/waveと、依存調整後のタスク内の値を区別する。|
|作れる・操作できること|固定ケースを選び、単純順・Namespace調整後・CRD調整後を比較する。|
|検証方法|実装前の手追跡表を、固定版実装とPython模型の結果に対応づける。|
|実務判断|宣言のwaveだけで判断せず、依存の名前・group/kind・target有無を確認する。|
|前提|Kubernetesのkind/group、metadata.namespace、CRDのspec、Desired/Live、前単元のphase/wave。|
|次の一歩|今回の模型外であるtask生成、実適用、Health、削除の条件を分けて整理する。LIVE追試は別工程。|

## 1. 先に予想する

`namespace-cross-phase` には、次の2タスクがあります。

|資源ID|kind / name|参照する名前空間|入力phase|入力wave|
|---|---|---|---|---:|
|prepare|Job / prepare|lesson|PreSync|−2|
|ns|Namespace / lesson|なし|Sync|5|

単純な比較ではJobが先です。予想してから答えを見てください。

- Namespaceは後ろのままか、Jobの前へ動くか。
- 前へ動くなら、タスク内のphaseとwaveは何になるか。
- 入力manifestそのものを書き換えたことになるか。
- Namespaceが初めから先にある場合も、同じ上書きが起きるか。

## 2. 操作して対照する

このディレクトリで実行します。Python標準ライブラリだけを使います。

```sh
# まず単純順だけを見て、調整後を予想する
python3 -B model.py --case namespace-cross-phase --view simple

# 入力値と有効値を残した3段階の表を比較する
python3 -B model.py --case namespace-cross-phase

# NamespaceとCRDが両方ある例へ進む
python3 -B model.py --case namespace-then-crd
```

`--json` を付けると、参照位置の記録、移動前後のindex、上書きされた値まで読めます。入力は[fixtures.json](fixtures.json)の5ケースだけです。任意のmanifestを読み込む機能ではありません。

|ケースID|観察する境界|
|---|---|
|`namespace-cross-phase`|後ろのNamespaceを前へ動かし、タスクのphase/waveを合わせる。|
|`crd-group-match`|CRDはgroupとkindの組で対応づける。同じWidgetでも別groupとは一致しない。|
|`dependency-already-first`|依存がすでに先なら、入力waveと参照元waveが違っても上書きしない。|
|`namespace-then-crd`|Namespaceの調整結果を使って、その後にCRDを調整する。|
|`target-missing-boundary`|targetのないタスクを参照元にも依存にも使わない。未解決の依存を補う処理ではない。|

## 3. 原典と実装を確認する

対象はv3.5.2、commit `e258ee23c3e52266d407572f4bcdfe7d9ed36cb5` の [gitops-engine/pkg/sync/sync_tasks.go](https://github.com/argoproj/argo-cd/blob/e258ee23c3e52266d407572f4bcdfe7d9ed36cb5/gitops-engine/pkg/sync/sync_tasks.go) です。

- `Less`：phase、wave、kind、nameの順で比較する。
- `Sort`：単純整列の後、Namespace、CRDの順で `adjustDeps` を呼ぶ。
- `adjustDeps`：targetのあるタスクを前から読み、最初の参照位置を記録する。対応する依存を後で見つけたとき、その参照元の直前へ移し、依存タスクのphaseとwaveOverrideを参照元に合わせる。

Namespaceはcore groupの名前、参照側はmetadata.namespaceで対応づけます。CRDはspec.groupとspec.names.kind、参照側はgroupとkindです。CRDのmetadata.nameが似ているだけでは対応しません。

公式raw URLの読取は1回で成功しました。[source-review.json](source-review.json)に取得経路と行locatorを記録しています。元のraw byte列をファイル取得していないので、そのSHA-256は未取得です。Argo CDのGoコードをビルド・実行した証拠ではありません。

[model.py](model.py)は、今回の固定入力に必要な比較と2回の走査だけを実装しています。Kubernetesの全型判定、manifest解釈、task生成を実装したものではありません。

## 4. 答え合わせ

[hand-oracle.json](hand-oracle.json)と[固定時点の記録](hand-oracle-lock.json)は、模型と検証器を作る前に保存しました。

|ケース|単純順|Namespace調整後|CRD調整後|上書きされた有効値|
|---|---|---|---|---|
|Namespaceが後ろ|prepare → ns|ns → prepare|同じ|ns：Sync/5 → PreSync/−2|
|CRDのgroup対応|other → wanted → crd|同じ|other → crd → wanted|crd：Sync/3 → Sync/−4|
|Namespaceがすでに先|ns → job|同じ|同じ|変更なし。nsはSync/−3、jobはSync/0。|
|NamespaceとCRD|custom → config → ns → crd|ns → custom → config → crd|ns → crd → custom → config|nsとcrdがPreSync/−2になる。configはSync/−1のまま。|
|targetなしの境界|old-reference → use-ghost → other-ns → ghost-live|同じ|同じ|変更なし。依存が満たされたという判定ではない。|

2例目では、otherは `other.invalid/Widget`、wantedは `demo.invalid/Widget`。CRDが定義するのは後者なので、wave −6のotherへは合わせません。

4例目では、customとconfigが同じNamespaceを参照します。先に見つかったcustomを基準にするため、Namespaceはconfigのwave −1へは合わせません。その後のCRD走査は、Namespace調整後の順で行います。

5例目では、old-referenceとghost-liveにtargetがありません。前者を参照元として登録せず、後者をNamespace依存としても動かしません。これは `Sort/adjustDeps` の境界だけの例です。live-only資源のprune順や、実適用の可否を検証した例ではありません。

**入力値は変えていません。** 模型で変えるのはタスク内の有効phaseとwaveOverrideです。Namespaceのmanifestへhook annotationを書き足した、Jobになった、先にHealthyになった、という意味ではありません。

## 5. 検証結果と実務判断

```sh
python3 -B verify.py
```

通常コマンドは保存原票を変更せず、手追跡・模型・ソース同一性を照合します。模型の原票を新規保存する入口は `--record` ですが、既存原票の上書きは拒否します。

5ケース・15タスク入力・2走査合計30訪問・依存移動4件が手追跡と一致しました。期待した入力拒否8件、誤った出力の検出5件も成功しています。[実行原票](observations/model-check.json)は軽いPython模型の実行記録です。時間は負荷試験・容量測定の値ではありません。[制作状態](observations/status.json)に未実施項目も記録しています。

同期順が予想と違うときは、まず「入力のwaveだけを見ていないか」「先に参照する資源がないか」「名前空間の名前やCRDのgroup/kindが一致するか」「targetが存在するか」を確かめます。調整後に前へ動いたことと、実際のAPI適用や準備完了を分けて判断してください。

## 6. 限界

任意の依存グラフを解く一般schedulerではありません。cycle検出・解決、topological sort、繰り返し走査による収束を保証しません。2回の指定された調整と、固定した一意のキーを持つ例だけを扱います。

同一sort keyの順序、不正CRD、複数CRDの衝突、任意groupの同名kind、target/live選択の全分岐、getSyncTasks、dry-run、prune、hook実行、Health、権限・API障害は未対応です。今回ブラウザ・画像・LIVEは使わず、画像QAは未実施です。既存repo・前単元・共有計画・受入台帳・統合状態は変更していません。[COVERAGE.md](COVERAGE.md)と[Skill](SKILL.md)も参照してください。
