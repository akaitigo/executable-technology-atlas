# 検証記録

独立期待をcontract.jsonに事前固定し、2026-10-05にNode全列挙と実IAB操作を取得しました。全分野網羅0、入口追加0、Subject/Atlasはincomplete。実通信・ランダムsample・製品profile適合・訂正・認証は未検証です。

## 実行原票

- [現在のNode原票](observations/node-attempt-02/raw.json)：16message×128mask＝2,048条件、128種類のreceived入力、150,040 assertion（6負例を含む）。Node v25.2.1、V8 14.1.146.11-node.14、darwin arm64。独立GF(2)乗算oracleで符号語・剰余・全除算traceを照合。
- [現在のIAB原票](observations/browser-attempt-01/raw.json)：Chrome 154.0.0.0、日本語、1280×720、DPR2。10実行・16 checkpoint、各実行attempt1/retries0。8正常算法実行と2入力契約拒否を別集計。正常・検出・未検出・不正入力・正常復帰・Skill経由の別実行を含みます。
- [checker原票](observations/check-attempt-01/raw.json)：156,895照合、12改ざん負例を拒否。負例の内部走査1,553,686照合は正常ケース数ではありません。DOM bit・除算行・途中状態・受信判定・harness比較・日時・run ID・Source 13件のdigest・16画面hashを検査。
- [以前のNode原票](observations/node-attempt-01/raw.json)は保存。Browser取得前にcheckerのNode例の表示labelとUI入力の構造差を修正し、Sourceが変わったため全Node列挙を再取得。算法の期待値・閾値・条件集合は変更していません。旧原票を現在Sourceへdigestだけで再固定していません。

各messageの非零127maskは未検出15・検出112。単一bit7個とspan≤3の23個（内部0あり・span1含む）は全検出。mask0001011では剰余000でもpayload0000→0001。これは独自有限規約の全列挙結果であって、実通信確率ではありません。

## 実画面と操作

[反例のbit・除算・元message比較](observations/browser-attempt-01/skill-undetected-comparison.jpg)、[反例の途中状態](observations/browser-attempt-01/undetected-1.jpg)、[span3の検出](observations/browser-attempt-01/short-burst-0.jpg)、[8bit maskの拒否](observations/browser-attempt-01/invalid-mask-0.jpg)、[正常復帰](observations/browser-attempt-01/recovery-normal-0.jpg)は実IAB capture。画面を合成・補正していません。反例は新しい実行から4位置を順に進め、Skill経由でも別runを作成しました。

Skillは同一agentによるnormal routeと、製品CRC・認証・実通信のunsupported route確認のみ。quick_validate成功は形式検査であり、独立Agent Forward Evalや利用者理解度の評価ではありません。

## 保存・read-only・後片付け

通常のverify/checkは原票を読み取るだけ。`--record`は新directoryへの保存だけを許し、既存directoryへの再保存は拒否します。既存成功・旧Source原票を削除しません。[標準権限でのpreview起動拒否](observations/preview-default-denied/raw.json)も保存。その後は明示的なhost許可のもと、所有moduleを動的loopbackだけで開きました。

最終read-only auditで通常実行前後の全file hash/mtime、既存directoryへの再保存拒否、元Hamming教材と直前BFS/DFSの70file hash/mtime、local link、秘密情報markerを確認します。自分のtab19/serverのみ終了し、利用者preview PID3901/port53478を残します。結果はaudit原票へ記録。旧Goal/Core/Gate・他module・Git・公開・Dockerは変更していません。

## 残す未達

E1製品profile、E2長いblock/burst/interleaving、E3暗号認証、E4実通信は全て未制作。多Browser/AT/実hardware、性能、独立Skill Eval、学習者理解度も未評価。元教材の限界と今回の増分を[scope.json](scope.json)へ明記しています。
