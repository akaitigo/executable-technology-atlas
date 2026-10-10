# Browser event loop教材の検証記録

## 問いと経路

同じ同期呼出し内で登録したPromiseと2timer、追加microtask、意図したreaction例外/catchの順序を実Browser iframeで比較します。予想→操作→比較→実装/原典→回答。Node checkerの合成fixtureは期待値検査だけで、Browser/Node Runtimeを実行した証拠ではありません。

## 固定期待値

| case | callback label順 |
|---|---|
| basic | sync-start → sync-end → micro-parent → timer-first → timer-micro → timer-second |
| nested | sync-start → sync-end → micro-parent → micro-peer → micro-child → micro-grandchild → timer-first → timer-micro → timer-second |
| caught-error | sync-start → sync-end → micro-throw → micro-peer → micro-caught → timer-first → timer-micro → timer-second |

basicは追加0・delay0の境界、nestedは追加分とqueueのpeer、caught-errorは意図的Errorとcatchを確認します。新Documentでのnested再実行も別原票。case.mjsはoracleを読まず、check.mjsは実順を期待値へコピーしません。経過msの正確さや上限はassertしません。

負例は追加分先送り、同期終了前timer、timer-micro欠落、stale source、非単調performance時刻、読込証拠欠落を拒否します。読み取り検査と明示recordを分離し、既存recordは保持します。

## 仕様・未確認

README/indexの一次資料locatorと4学習案へ接続。scope.jsonの主要8未教材領域は全て未教材のまま。新Documentは独立thread/process/security sandboxではありません。callback内のdomain instrumentationはBrowser全体のscheduler/paint/Network traceではなく、全engine/runtimeを保証しません。

## 実QA原票

2026-10-05 15:11:36.020–15:12:59.410 JSTに背景IABで操作した[原票](observations/browser-attempt-01/browser.json)を保存。basic/nested/caught-error/nested再実行の4run、誤った先送り予想、回答3候補、展開した学習案のDOM snapshotがあります。各iframeは新しいtimeOriginとrun IDを持ちます。実行はmoduleがsource manifestのfetchを終えた後の同期呼出しで開始し、page全体の開始時刻と区別します。

環境はUA `Chrome/154.0.0.0`、Macintosh、言語ja。main 1280×720、iframe 1008×420。この背景IABでiframeの `document.visibilityState` はvisibleだったため、hidden page throttlingの実測とは呼びません。loadingにはmanifest HTTP200/application/json、scriptとDocument path、source9ファイルのhashを記録。各callbackはsequence/label/kind/実日時/performance経過を記録します。複数eventが同じ時刻になる観測も保持し、丸められた時計から時間分解能を保証しません。

[独立checker結果](observations/check-attempt-01/check.json)はNode v25.2.1 / darwin / arm64で実行、Browser原票4run・200項目が成功。合成fixture146項目と負例6件の成功は、Browser実証件数へ足していません。README/indexの4学習案とscopeの8領域、local link8件も照合しました。

| Artifact | SHA-256 |
|---|---|
| Browser原票 | `996e0cce711c4001c3d8a73d86f2451404801ca6646184dc974e5b659eb5841e` |
| [nested画面](observations/browser-attempt-01/nested.jpg) | `8bacee691b0290620bf2d1f022b2a08b17fa63f6ccaa23dde51b2bead7de1c8a` |
| [caught-error画面](observations/browser-attempt-01/caught-error.jpg) | `62f883a55d04046e04220c0a54aa160cc3b306d5988c93f6bd2c0353327e4431` |
| [未実装学習案の画面](observations/browser-attempt-01/roadmap.jpg) | `d72aa78865c4a6734e5e22b68f72433c619b872ec24e3809e4e6f4ea17e54bc5` |
| 独立checker原票 | `268c1648016b7d290c1889888b0da524d81f3b910e2bed48960c856a40e0cc2a` |
| [同一AgentのSkill確認](observations/skill-control.json) | `75f44e5d24aefc1e771c3a4f856550058f06b7491ac73e9d7df56b62378baf95` |

全source/artifactとchecker自身のdigestはchecker原票にもあります。画像は実画面JPEG、1280×720、無加工のviewport抜粋。学習案の全表は一枚に収まらず、Browser原票のroadmap DOM/4rowで全体を確認します。hashはbinding/改変検出用で、内容の正しさや新規実行の代替にはしません。

## Skill・read-only・後片付け

module-local Skillのquick_validateは成功。同一Agentの通常routeでは既存basic UIをrun5として新Documentで実行し、固定期待順と一致しました。対象外のworker/process隔離・全Browser・0ms精度保証はscopeと未実装案へ案内し、実装を追加していません。独立Forward Evalは未実施です。

15:14:46 JSTの通常 `node check.mjs` と `node check.mjs --self-test` はexit0。既存directoryへ `--record check-attempt-01` を指定した意図的な失敗はexit1/EEXIST。その前後で教材内18ファイルの全hashが不変でした。初回sandbox内listenはEPERMで起動不能。一時的なloopback配信のみを許可された実行で再起動し、OSや永続的な権限設定は変更していません。

15:16:04 JSTには保存した4runのmain/iframe原票一致、現在sourceへのbinding、UI比較列、予想/回答のsnapshotを30項目で照合しました。学習案4rowとREADME/検証文書のlocal link存在も確認しています。

検証用tab8を閉じ、own server127.0.0.1:64605をCtrl+Cで停止（exit130）。`lsof -nP -iTCP:64605 -sTCP:LISTEN` はlistenerなし（exit1）。他taskのtab/processを停止していません。この専用directoryだけを変更し、Root文書/Core/Graph/旧Goal、他Subject、Docker/依存/OS/GitHub/global Skillへは触れていません。commit/push/公開、新Goal作成も行っていません。Portal/Coreの全体Gateはこの有限教材作業では未実行で、Subject全体を完成とは扱いません。
