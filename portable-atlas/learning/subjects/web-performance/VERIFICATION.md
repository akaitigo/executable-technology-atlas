# Layout / timer教材の検証記録

問い：同じ小gridを交互/batchedで更新し、実elapsedとgeometry値一致を分けて読めるか。120ms同期処理とtimer予約を区別できるか。固定oracleは計時の優劣を合格条件にしません。

## 実測の経路と範囲

2026-10-05 16:21:57.095–16:22:01.159 JSTの背景IABで、[最終Browser原票](observations/browser-attempt-04/browser.json)を取得。初期→8反復→0反復→-1拒否→timer probeの5観測、予想always-faster、3回答、展開したroadmap4rowを保持。実UAはChrome/154.0.0.0 / Macintosh、ja、viewport1280×720（UA表記でありbinary versionを別確認した値ではない）。実BrowserがDOMへ記録したJSON文字列rawTextをそのまま受け取り、ローカルで解析したrawも併記します。

同じtask-owned16セルで、通常8反復・warmup2 round・本測定5 round、mode順は交互。warmupも原票に残し除外条件を明示。各sampleは128read/128write、checksum14080、最終幅100/108/116/124pxの反復、height32px、fixture相対位置が独立oracleと一致。0反復はread/write/checksum0、全幅80px。-1は拒否して直前のgeometry/表示表を保持しました。

この最終runの本測定中央値はinterleaved 2.600ms、batched 0.400ms。最小/最大はinterleaved 2.500/2.700ms、batched 0.400/0.500ms（表示上の丸め値）。この小標本の観測であり速度保証ではありません。0反復の0msも捨てません。clockProbeは128読みの最小正delta（得られなければnull）を保存しますが、精度・統計的誤差の保証ではありません。reset/最終geometry採取は計時外、JS/style/geometry readが含まれるelapsedで純layout時間ではありません。JSのread/write回数はengine Layout event数ではありません。

timer実経過はidle（20ms予約）20.600ms、long-timer（100ms予約）102.600ms、blocking（20ms予約＋120ms同期spin）128.000ms。各caseにtimer-scheduled→work-start→work-end→handler-return→microtask→timer-firedの実performance.now/時刻を保持。blockingのmicrotask/timerは同期work-end以降。long-timerは同期占有0ms。これはtimer/microtask probeであり、実ユーザー入力・INP・paint/画面提示・OS全traceではありません。前runでも時間が異なり、再取得の揺れを保持しています。

## 独立検査

[現在SourceのNode原票](observations/node-attempt-04/node.json)は16:20:37.367–16:20:37.371 JST、Node v25.2.1 / darwin / arm64。純workload計画28項目が成功。Browser DOM/timing証拠ではありません。

[checker原票](observations/check-attempt-01/check.json)は16:22:11.967 JST、5観測・413項目成功。誤geometry、架空checksum、warmup削除、負elapsed、不正入力受理、block中timer、偽Sourceの7改変負例を拒否。合成改変はその不具合を実Browserで起こした証拠ではありません。Source11ファイルとchecker自身のdigest、README/indexの8未教材ID→4実験案、local link14件を照合します。厳密なelapsed=end-start等を維持し、batched勝利は合格条件にしていません。

16:23:41.025 JSTに通常verify/checkはexit0、既存node-attempt-04/check-attempt-01への明示recordはexit1/EEXISTで拒否。前後で教材内45ファイル全hash不変、全観測/回答のJSON.parse(rawText)=raw、Skill正常routeの14sample/checksum14080と未対応guarantee=falseを確認。これは当時の45ファイルで、後の文書追記は別の編集です。

## 原票と実画面のdigest

| 成果物 | SHA-256 |
|---|---|
| Browser原票（attempt-04） | `e00b5a3e6f4f5ede3d31f25df0179a1fe57eb09b8f4e26e37cd7d02ebf96b807` |
| Node原票（attempt-04） | `cd2bbffecdc4efbb721e0e9d2f2227296166055ff7021d9fcc657f9d7acaa178` |
| checker原票 | `8da517f96220384a944fed13643e05b3417f2039fd70a898e0155f968cf81c4c` |
| [通常測定画面](observations/browser-attempt-04/layout.jpg) | `e952fab8bdf28ce68c1f33a1c51692d5db01f4eefc1e7755fb7248570d111175` |
| [0反復画面](observations/browser-attempt-04/zero.jpg) | `5c296afec14e11e370ec99fbd1564d1184eaf2a48e64c563d22acb25e7963b2b` |
| [timer反例画面](observations/browser-attempt-04/probe.jpg) | `860a73235d533402f4455a6ba44b2d89d1adfeffc7b680cbf2398c18760e82b6` |
| [roadmap画面](observations/browser-attempt-04/roadmap.jpg) | `c0c7c75183ec6611150167b656cb45e0044f0c5d1f6975a5daa457227e41ac96` |
| [更新順序図の実表示](observations/browser-attempt-04/flow-diagram.jpg) | `3bc4ce4a8f24c7066e94774c1f99b84808af8beb92f53bb438e782454ddd9847` |
| [同一Agent Skill確認](observations/skill-control.json) | `8519103740397341150e19d71994883d912aa3e83ba8218a5624b17d067ff5eb` |

媒体は実viewportの無加工JPEG1280×720。通常/zero画像は全10行とsummaryが読めますがgrid上部は見切れます。全16boxは原票の実geometryで検査。長いroadmapは一枚に収まらず全4rowはDOM snapshotで確認。図は独自の説明図の実表示で、engineのtraceではありません。[初期画像](observations/browser-attempt-04/initial.jpg)の保存成功も確認済み。

## 失敗の保持と修正

- [初回listen拒否](observations/listen-failure-01.json)：通常sandboxでEPERM/exit1。許可された同session一時loopbackのホスト審査を利用し、設定/永続権限を変えていません。
- [初回Browser UI失敗](observations/browser-attempt-01/failed-ui.json)：実geometry/elapsedは採取できたが、getElementByIdへ子selectorを渡したためnull/replaceChildren例外、表示表0行。DOM selector検索へ修正し実再実行。原票と画像を保持。
- [採取集約漏れ](observations/record-aggregation-failure-01.json)：[attempt-02](observations/browser-attempt-02/browser.json)はobservations0。REPL helperが旧recordを保持したと診断し、object/helperを同一実行内に固定して全実操作をやり直し。文字出力から成功原票を組み立てていません。
- [数値転送の不整合](observations/numeric-transfer-failure-01.json)：[attempt-03](observations/browser-attempt-03/browser.json)ではelapsedとend-startの差が約5.68×10⁻¹⁴msとなりstrict checkerが拒否。object転送の丸めと推定し、Browser内のJSON文字列を保持・ローカル解析する採取方式で全実操作を再取得。期待値/tolerance/速度条件を緩めず最終attempt-04が通過。

各修正前のNode attempt-01/02/03、Browser原票/画像は削除せず歴史的証拠として保持し、現在Sourceの成功には使いません。Source/Harness更新はdigestだけの追記にせず実Node/Browser再実行しました。

## Skill、cleanup、残る範囲

専用Skillはquick_validate成功。同一Agentの通常routeは固定8反復を実UIのEnterで実行し、trusted click、14sample、全checksum14080、geometry一致を確認。未対応の本番LCP/INP全面保証・RUM収集はE1–E4へ案内し外部収集なし、guarantee=falseと記録。独立Forward Evalは未実施です。スキルの方針に従い、実測/合成負例/未実装案を分けて記録しました。

own IAB tab11を終了。own server127.0.0.1の53692/54029/54144/54371はCtrl+Cで停止（exit130）、全portのlsof検査は出力なし/exit1。他taskのtab/processへ触れていません。

専用directory以外のPortal root README/docs、Core/Graph、旧FE repo/Goal、他Subjectは変更していません。Docker、新依存、外部サービス、OS/GitHub設定、新永続権限、global Skill install、commit/push/公開、新Goalはありません。Portal全体Gate/Core auditは未実行で、この有限教材をSubject/全体Goalの完成とは扱いません。主要8未教材→4案、LCP/INP/CLS、RUM、network、assets、engine trace、workers、memory、性能CIと運用は未実装/未実証です。
