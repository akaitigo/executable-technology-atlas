# Syncedとhealthを分ける2段階gate

読む順は[前: driftと宣言](../../../subjects/gitops-continuous-delivery/README.md) → この単元 → [次: rollbackとdata互換](../../ci-cd-release-engineering/rollback-data-compatibility/README.md)。元Subject READMEの健康・段階releaseの次実験を、既存Python3.9.6 stdlibの有限模型へ進める。元Subjectや共有Portalは編集しない。

前提はdesired/actual、generation、reconcile。まず「宣言一致でもDegradedなら次stageへ進むか」「rollback宣言でactualも即時に戻るか」を予想する。Python模型を実行し、位置を変えて原票を追い、一次資料・実装・手表を読み、答えを開く。health JSONはHealthy/Degraded/Progressingだけを許可し、非文字列・未知値を実行前に拒否。healthは固定fixture入力で、probe結果ではない。

|条件|stage1 desired/actual|health|stage2開始数|
|---|---|---|---:|
|正常gate|v2/v2|Healthy|1、再gateも1|
|不健康gate|v2/v2|Degraded|0|
|進行中gate|v2/v2|Progressing|0|
|desired一致のみ故障|v2/v2|Degraded|1|
|rollback|v1/v2→v1/v1|Degraded→Progressing→Healthy fixture|0（既定Degraded）|

publish-v2ではgeneration2・desiredv2・actualv1。reconcile-v2でactualv2になっても、healthはProgressingのまま。健康観測fixtureを別eventにする。正しいgateは一致とHealthyを確認し、stage2は一度だけ開始する。desired一致のみ故障はhealth条件を落とす意図的bug。

rollbackではgeneration3として旧payload v1を宣言する。その瞬間actualはv2、次reconcileでv1へ変わる。最後のHealthyは入力模型の追加fixtureで、サービス復旧の測定ではない。UIの答えは全trace終端を示し、位置は下の選択eventだけを変える。入力healthを変更すれば開始数も変わり得るため、答えは実eventから表示する。

[Argo Resource Health](https://argo-cd.readthedocs.io/en/stable/operator-manual/health/)はresource固有のhealth判定とHealthy/Progressing/Degradedを説明する。Applicationのhealthと子孫のhealthは自動的に同一とは限らない。[Sync Waves](https://argo-cd.readthedocs.io/en/stable/user-guide/sync-waves/)はout-of-sync/unhealthyの最初のwaveから処理する仕組みを説明する。この2stage模型は製品のwave実装、hook、retry、probeを再現したものではない。

```sh
python3 -B verify.py --record attempt-01  # 未使用attemptだけ
python3 -B verify.py --seal-record       # QA後の明示seal
python3 -B verify.py                     # 実再計算、file保存なし
python3 -B route.py                      # 同じ限定checker
python3 -B serve.py                      # 動的127.0.0.1、終了Ctrl-C
```

[手表](hand-oracle.json)はrunner実装前に固定したevent/rev/health/count表。[独立oracle](oracle.py)はrunnerをimportせず、literal表と別Synced期待表を照合する。7条件29event、host拒否8入力、原票改変6種を検査する。failureは実Python RuntimeErrorの意図注入で、実Argoの自然障害ではない。初回raw/receiptを残し、UI QA後にcurrent source/artifactをseal。通常checkerとrouteの全file hash/mtime前後一致を保存する。

未検証: 実Argo/cluster、readiness/liveness probe、health観測の遅延/真偽、DB/schema/data rollback、availability、無停止、永続履歴、並列controller、署名、retry/timeout。次の実験はhealth観測のstale拒否、部分reconcile失敗の再試行、実probeとdata互換の接続（いずれも未実施）。この追加はGitOps全分野のcompleteではない。install・公開・commit/push・Core gateは本専有制作の範囲外。
