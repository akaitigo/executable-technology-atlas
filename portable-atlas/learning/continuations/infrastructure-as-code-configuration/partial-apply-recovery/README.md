# Apply失敗のあと、何が残った？

[元単元](../../../subjects/infrastructure-as-code-configuration/README.md)の次実験④ partial failure/recoveryを制作した追加単元です。JSONのdesired/observed、plan、apply、revisionを前提に、途中失敗を「変更ゼロ」と解釈せず、実stateから新planを作る判断を学びます。原入口97件と既存原票を変更せず、singleprocess snapshot検査やStorageのlost updateを再実装しません。

## 先に固定した予想

3つの合成resourceを `base → config → service` の順でcreateします。baseはzone=task-local、configはtext=v2、serviceはreplicas=2。初期stateはrevision0/resource空。依存順を宣言に固定し、resourceごとに実JSON fileを保存しrevisionを1増やす独自契約です。

| 条件 | 最初のapply exit | 保存される途中state | 盲目replay | 再観測後の新plan | 最終state |
|---|---:|---|---|---|---|
| normal | 0 | base/config/service、revision3 | baseの重複create拒否22 | actions0 | 同じ3件 |
| before-second | 70 | baseだけ、revision1 | 同じ拒否22、state不変 | config/serviceだけcreate | 3件、revision3 |
| after-second | 71 | base/config、revision2 | 同じ拒否22、state不変 | serviceだけcreate | 3件、revision3 |

[contracts.json](contracts.json)と独立checkerの手書きstate/遷移は、最初の実行より前に固定。checkerはplanner/実行実装をimportしません。変更後faultはconfigの保存と再読取の後なので2件残ります。変更前faultはconfigの書込前なので1件です。failureの名前だけでなく、どの副作用まで確認できたかを読みます。

## 予想 → 操作 → 比較 → 原典/実装/raw → 答え

[UI](index.html)で、rollbackされたか・盲目replayできるか・新planが何を含むかを予想します。段階を進めて、初期plan → first apply失敗とpartial → blind replay拒否 → refresh/replan → recovery → no-opを読みます。各段階は保存した実command/実fileの再生で、ブラウザがapplyを実行しません。

比較後に[実CLI](store_cli.py)、[採取driver](runner.py)、[独立checker](checker.py)、[原典locator](sources.json)、画面のrun-specific raw/command/fileリンクへ戻り、答えを開きます。

```sh
# 通常検算はsocket/storeを変更しない
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
# 明示採取だけが専用storeに実ファイル変更を行う
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record
# 保存原票のUIをloopbackでpreviewする
python3 -u -m http.server 0 --bind 127.0.0.1
```

表示された動的portを使い、serverはCtrl-Cで終了。既存Node PID3901/port53478を使わず、止めません。引数なしrunnerはexit1で更新拒否。明示recordは新しいobservations/run directoryに3つの専用storeを作り、旧rawを上書きしません。child commandは各5秒timeout。stdoutのUTC付き実trace、stderrのInjectedFault/DuplicateCreate、exit、Python/OS、input/source/全artifact SHA256/sizeを保存します。予期しないfailureでも採取済みcommand/fileは残り、記録が中断すれば成功pointerは更新しません。

## 何が実行されるか

各caseは実JSON storeで、別Python processがplan/apply/refreshを実行します。original-planは3create。途中失敗後、driverは同じstoreを読みpartial.jsonへ保存し、**storeを初期stateへ戻しません**。blind replayは同じoriginal-planを使い、既存baseに対する非冪等createの重複を拒否。その後refreshが実storeを読み、新planが存在するdesired resourceを除外して未適用suffixだけcreateします。最後にもう一度plan/applyしactions0、store hashとmtime不変を確認します。

正常でも古い3createをblind replayすれば拒否になります。ここで比較するのは非冪等commandの再実行と、同じ宣言から現在stateを照合するreconcileです。全てのprovider createが重複拒否する、Terraformがこんな盲目replayをする、とは主張しません。

## 実務判断と限界

1. exit非0を見たら、失敗したstepと確認済み副作用を分ける。先行resourceは残る可能性があり、依存resourceがまだなくてサービスは不完全かもしれない。
2. 失敗traceと部分stateを保存する。見栄えのために初期stateへ戻さない。「rollback済み」と報告するなら、その処理と実結果の別証拠が必要。
3. 実stateを再観測し、desiredとの差から新planをレビューする。既に成功したcreateを繰り返すと、重複・副作用・費用につながる場合がある。
4. 未適用分だけreconcileして、もう一度no-opを検査する。ただしJSONのconvergenceだけではreadinessや業務正常、秘密値、正しい権限を保証しない。

単一writer、順序固定、create-only、resource数3、各resourceの副作用と記録を同じJSONへ書く模型です。更新/replacement/delete、実providerのrefresh、Terraform state/backend/lock、network timeout後の成功不明、操作とcheckpointの間のcrash、fsync・atomic rename・durability・分散transaction・rollback保証は未実行。faultは第2actionの書込前/保存と再読取後へ明示注入したもので、OS crashや実cloud errorを再現したものではありません。revisionは独自観測用で、Terraform state serialと同一ではありません。

## 公式原典への接続

[Terraform apply / Errors during an apply operation](https://developer.hashicorp.com/terraform/cli/commands/apply#errors-during-an-apply-operation)は、部分変更が残る失敗と復旧判断を読む入口です。[plan / Introduction・Planning Modes](https://developer.hashicorp.com/terraform/cli/commands/plan)は観測と新planを考える入口です。保存plan/approvalやrefresh-onlyの実意味を独自CLIへ同一視しません。今回のrefreshはfileの再読取です。第三者本文は保存せず、URL/locator/bindingをsources.jsonに保持し、取得不能URLも隠しません。

## 今回のcoverage増分と次の3実験（未実行）

増分はpartial apply前後の実store、失敗をrollbackと混同する誤り、blind create replay拒否、refresh/new plan/未適用suffix reconcile、2回目no-opです。全Subject/Atlas完成やformal deliveryは主張せず、[実測/実IAB/cleanup](qa/README.md)の有限受入だけを扱います。

| 残る問い・次入力 | 独立予想と観測 | 公式locator |
|---|---|---|
| 観測失敗/unknown | file adapterが正常/読取不能/未知属性の3状態を返すfixture。unknownをmissingと誤認してcreateしないことを手書きplanへ照合。 | plan Planning Options / refresh、元単元次実験① |
| 副作用済みだがcheckpoint未記録 | 専用resource fileとjournalを分け、create後journal前でchild終了。再観測で存在を発見し、再create/補償を勝手に始めず復旧planを比較。 | apply Errors during an apply operation、provider観測（製品追試は別） |
| 復旧planのレビュー | desiredの途中変更でrecovery planにdelete/replacementが加わる合成trace。元承認が新planへ適用される誤りと、新planレビューを比較。 | apply Saved Plan Mode / plan Planning Modes |

次実験は自動開始しません。本番Terraform/provider/cloudへの操作は別の明示割当が必要です。
