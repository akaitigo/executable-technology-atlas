# native ES modules教材の検証記録

## 経路と範囲

同じcounterを2つのimporterで読むnative ES modulesを実Browserで確認する一教材です。live bindingと数値コピー、初回評価、更新関数、代入拒否、HTTP読込/parse失敗を区別します。Nodeのfile loaderは別検査で、BrowserのHTTP/MIMEやerror nameの証拠へ代用しません。

学習は前提→主要概念→今回の操作/正常異常→実務判断→限界→一次資料と次実験へ進みます。README/indexの4実験案はscope.jsonの9主要未教材領域に対応しますが、未実装の計画です。cycle/framework/build tool等の実証ではありません。

## 原票の世代

初期のBrowser attempt-01とNode attempt-01は、学習導線追記前の実測として保持しています。Node attempt-02は導線追記後・検証文書配信追加前の中間原票。現HTML/配信Harnessの採用原票はNode attempt-03とBrowser attempt-02です。旧原票をhashだけ差し替えたり上書きしていません。

## 期待値と観測

| 操作 | 独立期待値 |
|---|---|
| initial / A +1 / B +1 | 両live 0→1→2、両snapshot 0 |
| delta0 / imported count代入 / namespace代入 | live 2維持。代入はTypeError |
| 同URL再import / NaN拒否 | counter評価1回、namespace同一、live2。NaNはRangeError |
| −1 / 失敗iframe2件 | live1。iframe失敗後もmainの評価/値は保持 |
| iframe後A +1 / 回答3候補 | live2へ更新可能。コピー/直接代入は不足、live+export元関数が適切 |
| 読込失敗 | Browser TypeError、別HTTP probe404/text/plain |
| 構文失敗 | Browser SyntaxError、別HTTP probe200/text/javascript |

Browserは15状態221項目と2隔離失敗を観測。期待値はUIの現在値から作らず、検査側の固定表です。操作区間内のfresh domain eventとmodule評価ログを照合します。UIイベントの記録はdomain instrumentationで、OS/Network trace全体ではありません。

Nodeは9状態35項目を確認。欠落moduleはError/ERR_MODULE_NOT_FOUND、構文はSyntaxError。BrowserとNodeの異なる失敗分類を保持し、同一結果だと扱いません。

負例4件（snapshotをlive値へ改変、counter2回評価、loadingをSyntaxErrorへ変更、古いSource binding）を拒否。通常checkerはread-only、明示recordでだけ新規directoryへ保存します。既存record指定のEEXIST拒否時も全file hash不変を確認しました。

## 仕様の根拠と限界

[ECMAScript §9.1.1.5.5 CreateImportBinding](https://tc39.es/ecma262/multipage/executable-code-and-execution-contexts.html#sec-module-environment-records-createimportbinding-n-m-n2)、[§10.4.6.9 Module Namespace [[Set]]](https://tc39.es/ecma262/multipage/ordinary-and-exotic-objects-behaviours.html#sec-module-namespace-exotic-objects-set-p-v-receiver)、[HTML module map](https://html.spec.whatwg.org/multipage/webappapis.html#module-map)を2026-10-05に確認しました。コード/素材は独自実装です。

「1回」はこの同Document/同resolved URLのfixtureに限定。異なるURL/query/fragment/new Documentまで一般化しません。read-only importはexport object内部のdeep freezeではありません。iframeは同一originの別Documentで、security sandboxの保証ではありません。現在値のDOM反映は明示的render()で、module bindingだけで自動renderされません。

全Browser、cycle/TDZ/TLA、worker/他realm、framework、build tool、GC/Wasm、CORS/CSP/cache/offline、実性能/配信運用は未検証・未教材です。E1–E4はこれらに向かう実験の入口で、実行済みEvidenceではありません。

## 記録と後片付け

旧成功原票と意図した失敗fixtureは保持しています。旧Goal/Core/Graph、他repo/Subject、Portal root文書、Docker、依存、OS/GitHub設定、global Skill、commit/push/公開は変更していません。

## 最終QA（2026-10-05）

現ソースの[Browser原票](observations/browser-attempt-02/browser.json)は14:55:15.421–14:56:00.652 JSTの15状態。環境はCodex背景IAB、UA `Chrome/154.0.0.0`、言語ja、1280×720です。時刻は記録開始/終了で、Documentのmodule評価時刻は原票内journalに別記しています。A/Bの現在値、snapshot、各評価1回、代入拒否、2つの隔離失敗、失敗後更新、回答を確認しました。

[Node原票](observations/node-attempt-03/node.json)はNode v25.2.1 / darwin / arm64、14:51:28.465–14:51:28.469 JSTの検査区間です。この区間の前に行われるstatic importの評価時刻はjournalに残り、process全体の開始時刻とは呼びません。[最新の保存原票監査](observations/audit-attempt-03/audit.json)は221項目、4負例を拒否。9未教材IDと4計画rowの対応、local link 10件の存在も確認しました。attempt-02監査も保持し、READMEのrecord例を未使用名へ修正した後、attempt-03へ新規記録しました。

[同一AgentのSkill確認](observations/skill-control-final.json)では既存UIのB +1で両live 2→3、両snapshot 0を確認し、対象外のcycle/framework/build tool/他runtime保証を未教材へ案内しました。`quick_validate.py`は成功。これは独立Forward Evalではありません。

| 原票/実画面 | SHA-256 |
|---|---|
| Browser原票 | `bd54eeadd885e8369db16f626b44aa5ccdd628a142cdec240727a51c37ea4009` |
| Node原票 | `2a35d97a16e9698add50f7623ed058af8c95279d1c67ca8ebe67e66cbbd97344` |
| [live参照画面](observations/browser-attempt-02/live-binding.jpg) | `2b5c58f8bffb23e79cf6d257c643f79557f1ac779d5a155e5aebf8f61f958727` |
| [隔離失敗画面](observations/browser-attempt-02/isolated-failures.jpg) | `f3ff4c4f4487abb097544d40949929d293898cfcbb3d8d8e26db49cfe5ee3e6a` |
| [学習案画面](observations/browser-attempt-02/roadmap.jpg) | `8527b89920adde8e3a34cc31e25971a944bd3f6979ec762a755017bd9c200e2a` |
| [学習案のDOM原票](observations/browser-attempt-02/roadmap.json) | `d3378b2dd069f778814fd9dcd6772c7324492031de5acbd1a1ec8c10d4ad0351` |
| 最新の保存原票監査 | `9573d91512b6dded7ff7ca4e05ecf73bed1342c18244b43d3dfe29573c8f2121` |
| Skill同一Agent確認 | `40c1cca0c93a9c927bb6cf66dcf27469e6c3f0d1f545aeeec0fde15298295987` |

画像は実画面JPEG、1280×720、無加工のviewport抜粋です。学習案の長い表の全行は一枚に収まらず、DOM原票で全4rowを確認します。Source 13ファイルの全hashと監査器自身のhashは監査JSONにあります。hash一致だけを実行成功とは扱いません。

検証用tab 7を閉じ、own serverの127.0.0.1:62386をCtrl+Cで停止（exit130）。`lsof -nP -iTCP:62386 -sTCP:LISTEN`はlistenerなし（exit1）。他タブ/processへは触れていません。今回の一教材の確認はSubject全体や旧Frontend Goalの完了ではなく、Portal/Coreの全体Gateもこの作業では実行していません。

14:58:46 JSTの通常 `node verify.mjs` / `node audit.mjs` はexit0。`node verify.mjs --record node-attempt-03` の意図的な既存directory指定はexit1/EEXISTで拒否され、その3実行の前後で当時の教材内32ファイルの全hashが不変でした。
