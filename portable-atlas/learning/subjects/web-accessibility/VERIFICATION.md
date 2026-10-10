# 一教材の検証記録

## 問い・経路・現在地

同じカウント操作で、クリック可能、Tab到達可能、キー操作可能、名前が伝わることを区別できるか。

日本語のnative HTML/CSS/JS教材を、Nodeのキー処理検査と背景IABの実DOM操作で確認しました。有限の一教材を制作・確認した結果であり、Web Accessibility Subject全体の完成でもWCAG適合証明でもありません。旧Goal/Core/Graphは変更していません。公開・commit・pushは行っていません。

実環境: Node v25.2.1 / darwin / arm64。IABでページが記録したUAはChrome/154.0.0.0、言語ja、viewport 1280×720。UAのMac OS X 10_15_7表記を実OS版と断定しません。Browser実測は2026-10-05 14:01:06–14:06:26 JST（原票はUTC）。

## 結果

| 操作・条件 | 実測 | 原票ID |
|---|---|---|
| native: Tab / Enter / Space | 到達し、0→1→2、focus-visibleと3px枠 | native-tab / native-enter / native-space |
| click-only div | Tabはdivを飛ばして到着点へ。クリックは0→1。button roleなし | click-only-tab-skips / click-only-mouse |
| role+tabindexのみ | Tabで到達、button role/nameあり。Enter/Spaceは0のまま | role-only-tab / role-only-enter / role-only-space |
| 修正版div | Tabで到達、Enter/Spaceは0→1→2。操作後もfocusが残る | repaired-tab / repaired-enter / repaired-space |
| 無効境界 | nativeはTab順から外れる。divは到達し、Enter/Space/実クリックすべて2のまま | disabled-tab / disabled-enter / disabled-space / disabled-mouse |
| 名前欠落 | 文字は見えるが、空nameのbuttonをrole queryで1件検出。Enterで0→1 | name-missing / name-missing-keyboard |
| 名前修正 | aria-hidden除去で空nameは0件、指定nameは1件 | name-restored |
| 回答4候補 | roleのみ/tabindexのみは不足、全部そろえたcustomは条件付き、nativeは適切 | quiz-role / quiz-tab / quiz-complete / quiz-native |

22観測・66期待値照合がpass。カウント期待値はページのreducerから生成せず、検査側の固定表から照合します。DOM snapshot、実イベント、入力説明と時刻を各観測に保存しています。

[Browser原票](observations/browser-attempt-01/browser.json)に、computed role/nameのlocator結果とnative AX treeを両方保存しています。native AX出力の`button unnamed`表記だけを名前空の根拠にはせず、`#unnamed`に対するrole queryの`name: ''`一致1件と修正後の指定name一致を照合しました。textContent/aria属性の推測ではありません。スクリーンリーダー読み上げの実録でもありません。

無効divのlocator `press` はツールのactionability待ちで止まり、対象へのキーを送信していません。状態を再確認後、Tabで到達した現在focusへnative inputのReturn/spaceを送りました。実キーイベントのtrusted=true、対象custom、count不変を保存しました。クリックはforceでlocatorのactionability待ちだけを外し、実マウスイベントを送っています。aria-disabledを消したり、DOM dispatchで疑似成功にしたりしていません。

## 検査と証拠の対応

- [Nodeキー処理原票](observations/node-attempt-02/node.json): 独立期待値表12条件。Space down/up、repeat、blur取消、focus喪失、disabled、無関係キーを含む。これはnative DOMの証明ではありません。
- [観測照合原票](observations/checked-attempt-01/node.json): 22観測を66期待値で照合。source digest一致。
- [時刻・入力監査原票](observations/audit-attempt-01/audit.json): 9キー区間、5 Tab遷移、2マウス区間を、その観測間に発生したfresh trustedイベントで検査。古いキーの流用、focus遷移欠落、名前修正の推測という3負例を拒否。
- 通常検査の `verify.mjs`、保存Browserを指定した `verify.mjs`、`audit.mjs` は全てexit 0。前後の教材全ファイルSHA-256集合が一致し、read-onlyを確認。
- `node --check keyboard.js` / `lesson.js` はpass。
- module-local Skillのquick_validateはpass。[同一Agentルーティング記録](observations/skill-control.json)では通常ルートが実Tab/Enterで不良0→修正1を示し、対象外のWCAG認証/全AT/dialog保証を行わない。これは独立Agent Forward Evalではない。

## 原票と画像のhash

全てSHA-256。実行Sourceと主要Artifactのdigest/byte数は[監査JSON](observations/audit-attempt-01/audit.json)へ保存。画像は実IAB viewport screenshot、JPEG 1280×720、無加工です。

| ファイル | SHA-256 |
|---|---|
| index.html | b1cff2a6c200724900c8d993701a4d65385d19408c8df1c3bd0fbd2823b381dd |
| keyboard.js | 02df86336388ddd48f142d074a3263641608221e1f2bfa3597be63fe159ee3fe |
| lesson.js | 6dafefbee669c9f4a1cb3396c5da05d8a9dfde3588e912ffc784be133bcaf90c |
| Browser原票 | 4b81c4daa56fe11b20fe4152132ecb6f8cd6cce3c86469f254e3f909991793b9 |
| comparison.jpg / 77,011 bytes | 69af79af159f420917992b0637a6bf46121ab346d768c8da6b552fb0af73a9ed |
| name-missing.jpg / 77,412 bytes | 811040edc2b695263acaf1bb77fbfeec9b9fd427d2034c603461cab814dbf050 |
| 観測照合原票 | 45921aaa55003f1304f0ea41fa22cb34172ce33f741a24fdb9d94c4fdc56eacb |
| 時刻監査原票 | 80753a78ad7b4e3b4fb62a644d9073fbc8da65fd30e1e867444885c89bda92d1 |
| Skill control | 7e81503fceb2ff3669662aca1c6aaf2b5fdb21b12ffa1a56209bd72613e7b78e |

![比較とfocus枠の実画面](observations/browser-attempt-01/comparison.jpg)

![文字が見える名前欠落例の実画面](observations/browser-attempt-01/name-missing.jpg)

画像単独ではキー入力の経路やcomputed nameを証明しません。原票のイベント/role queryと併読してください。

## 修正・失敗保持と後片付け

初期保存のENOENT、sandbox loopback待受のEPERM、CUA読み取りscopeでnavigator取得不可、再開変数の未初期化、無効locator入力の停止を[運用失敗記録](observations/operational-failures.json)へ残しました。正確な時刻を取得できなかった失敗には時刻を補っていません。

初期Node原票はキー検査passですが、以後の環境/focus観測追加前のsource digestなので現UIの証拠には採用しません。削除せず、Node attempt-02と実Browser記録を採用しています。[11状態時点の部分checkpoint](observations/browser-attempt-01/browser.partial.json)も未完記録として保持しました。

専用IABタブをcloseし、自分のloopback serverをCtrl+Cで終了（exit130）。他担当のタブ/Chrome/サーバー/資源は操作していません。新規依存、Docker、OS設定、グローバルSkill、Core/Graph/Goal、ルート文書、他Subjectは変更なし。

## 未測定・未制作

実VoiceOver/NVDA/JAWS/Braille、他Browser/OS、物理キーボード長押し、blur中のSpace取消の実Browser試験、WCAG適合監査は未実測です。Node境界検査と区別します。フォーム、複合widget、動的通知等は[scope.json](scope.json)の未制作領域へ分離しています。Subject全体の目標は未完です。
