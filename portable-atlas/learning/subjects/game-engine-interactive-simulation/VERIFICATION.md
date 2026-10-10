# 検証記録

有限unitを実行・照合しました。Subjectは **incomplete**。実engine、native device、一般的なphysics/network決定性、全体Goalは検証していません。Root/他Subject/旧FEリポジトリ、Core Gate/Graph、Git/publicationには変更を加えていません。

## 実行原本とbinding

- 現行[Node原本](observations/node-attempt-02/raw.json)：2026-10-05T08:55:20.848Z〜08:55:20.855Z。Node v25.2.1 / V8 14.1.146.11-node.14、darwin arm64、11入力、1,897比較assertion。engine製品の実行ではなくtoy recurrenceの実Node実行。
- 現行[Browser原本](observations/browser-attempt-02/raw.json)：QA収集08:56:14.040Z〜08:56:35.828Z。Chrome/154.0.0.0のUA、language ja、1280×720、DPR 2。11操作記録（全11入力、frame切替、keyboardを含む）。runごとの時刻・全frame/step・入力・Source13 member hash・rawText・図/表/clock・Screenshot hashを保持。
- [checker記録](observations/check-attempt-02/raw.json)：5,842 positive比較assertion、10改ざん負例を拒否。negative中の失敗地点までの23,811比較は別計上し、成功試験数へ加えない。
- Source集合：[sources.mjs](sources.mjs)。[checker](check.mjs)自身を含む13 memberを現行原本へbinding。case追加に伴いNode/Browserを別directoryへ実再実行し、digestだけの更新をしなかった。
- [初回Node](observations/node-attempt-01/raw.json)・[初回Browser](observations/browser-attempt-01/raw.json)・[初回checker](observations/check-attempt-01/raw.json)は10入力時点の旧Source原本として保持。現在Sourceの検証Evidenceとは扱わない。初回BrowserのQA収集開始は最初のrun後なので、操作全体の開始時刻ではない。2回目は開始後に全UI操作を再実行した。
- [通常preview拒否](observations/preview-default-denied/raw.json)も保持。個別exit=1、listen EPERM/127.0.0.1。toolに開始/完了時刻がないためnull、pathを含むstackは保存せず原本error excerptを保存した。

## 内容の確認

実Browserの床入力ではvariable y=8.2、fixed y=6 / grounded=true。fixedのtick 8の候補6.624が帯[6,7]へ入る。高速反例はfixedの4→8も帯を飛び越え、接地しない。成功画面へ書き換えず両方のcounterexampleを保持する。

pause-retainはvariable y=.4、fixed y=0、余り10 ms、破棄190 ms。tab-capはvariable y=4.42、fixed y=4.08、accepted110、fixed simulated100、破棄1900、余り10 ms。pause-resumeと19＋1 msも全入力操作で実行。負のdeltaはframe/stepが空、final=nullで事前拒否。

![薄い床の実Browser画面](observations/browser-attempt-02/floor-balanced.jpg)

図は記録されたstateを描いた説明図。screenshotは実UIで取得した画面だが、動画・実frame latency・game engine traceではない。primary sourceは設計を読む入口で、Box2D/Godot/Unityを実行したEvidenceではない。

## Skillと原本保護

quick_validateはexit 0 / `Skill is valid!`。同一agentのsupported routeはrunへfocusしてEnter、unsupportedな実engine CCD/network replay要求はE1/E4へ案内し未実行と明示。独立Forward Evalではない。

通常の `node verify.mjs` / `node check.mjs` は書き込みなし。原本の新規生成は明示 `--record observations/NEW-ID` の時だけ。既存directory拒否・前後hash照合の実結果は `observations/read-only-audit/raw.json` に保存する（監査report自身は自己hash循環のため集合から除外）。

教材専用tab 15を閉じ、Node sessions 70800/62928をSIGINTで停止（exit130）。対象port 62079/62460のlsof LISTEN確認はexit1・出力0で、待受は残っていない。依存追加・OS/GitHub設定変更・外部公開・削除なし。全体Gate未実行であり、この有限unitの検証からRepository/Subject完成を推定しない。
