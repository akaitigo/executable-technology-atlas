# 時間刻みで変わる運動と衝突

同じ200 msを100＋100と10＋190に分けて、variable explicit Eulerと20 ms fixed-step accumulatorを実Browserで比較する有限教材です。Subjectは **incomplete**。ゲームengine製品は使いません。

## 前提 → 概念 → 操作

必要な前提は秒とms、位置・速度・加速度、配列とloopです。下向きを＋、位置→速度の順に更新します。

1. `node serve.mjs` で表示された動的127.0.0.1 URLを開く。外部公開ではない。
2. 同じ合計時間で最終位置が変わるか予測し、自由落下2入力を操作する。
3. 薄い床2入力で衝突の取りこぼしを比べ、「次のframe状態を見る」で図を戻す。
4. 高速反例・pause・cap・19＋1 ms・負のdeltaを操作し、答えを開く。
5. [入力](cases.json)、[通常と異常の実装](model.mjs)、[独立oracle](oracle.mjs)、元のraw記録を読む。

## 仕組みと独立計算

variableはaccepted frameごとに `y += v * dt; v += g * dt`。fixedは整数msのaccumulatorへaccepted deltaを足し、20 ms以上ある間だけ同じ更新をします。余りを保持し、pause中は新しいdeltaを全て捨てます。再開時のcatch-upはしません。frame capによる破棄も明示します。全入力を事前検証し、負のdeltaは部分更新前に拒否します。

oracleはruntimeの更新loopをimportせず、任意刻みの閉形式 `y=y0+v0*T+g*(T*T−sum(dt*dt))/2` と `v=v0+g*T` をprefixごとに計算します。fixedは `T=n*h`、tick終端位置が初めて床帯に入るnを探索します。これは衝突の一般解析解ではなく、この点と有限帯のtoy判定に対する独立step oracleです。位置・速度の絶対誤差許容は実行前に **1e-10 toy unit**、clock/tick/flag/IDは厳密一致。[検証器](validation.mjs)で全frameと全stepを比較します。

| 比較 | variable | fixed 20 ms |
|---|---:|---:|
| 自由落下100＋100 ms | y=8.2 | y=8.36 / 10 tick |
| 自由落下10＋190 ms | y=8.038 | y=8.36 / 10 tick |
| 同入力＋床帯[6,7] | 終端が帯を飛び越す | tick 8の候補6.624を検出しy=6へ |
| v0=200、g=0＋同じ床 | すり抜け | 4→8の終端も帯を飛び越す |
| raw 10＋2000 ms、cap=100 | accepted110 ms | simulated100 ms / 余り10 ms |

床なし連続解析解は200 msで8.4。fixedも厳密解ではありません。床は**有限帯にpoint終端が重なった時だけ止める**特殊な判定で、無限半空間のground、剛体、CCDではありません。すり抜けは失敗反例として正常に保存します。pause-retainでは最初の10 msを貯め、次frameのpauseで190 msを捨てても余り10 msが残る境界を実行します。全11入力です。

## 実務への判断と制約

frame変動からphysics tickを分離する設計と、衝突検出の能力を混同しないこと。速度・step・形状で判定の成否が変わります。capは時間を捨てる選択であり、frame backlogを処理した証明ではありません。現教材は固定2 frame fixtureを実Browserで計算しますが、実rAF間隔、tab visibilityイベント、描画interpolation、CPU/GPU budget、native input、audio、engine物理精度・決定性を測りません。Nodeは同じtoy実装の別runtime照合で、実engineの代替検証ではありません。

## 次の未制作単元

[機械可読Coverage](scope.json)に各領域と実験を接続しています。いずれも未実施です。

- E1 実engine physics：固定versionでthin-wall/high-speed/contactsとCCDを比較し、衝突時刻・penetrationを測定。剛体・joint・contact・substep精度へ拡張する。[Box2D Simulation](https://box2d.org/documentation/md_simulation.html)、[Godot Physics introduction](https://docs.godotengine.org/en/stable/tutorials/physics/physics_introduction.html)
- E2 Scene/asset所有権：load/unload・欠損asset・破棄後callbackを実engineで観測。scene/ECS、asset lifecycle、native devicesの学習経路。[Godot SceneTree](https://docs.godotengine.org/en/stable/tutorials/scripting/scene_tree.html)
- E3 Input/audio/render：input→tick→render trace、interpolation、audio pause、slow frame budgetとrelease buildを測定。[Godot InputEvent](https://docs.godotengine.org/en/stable/tutorials/inputs/inputevent.html)、[HTML animation frames](https://html.spec.whatwg.org/multipage/imagebitmap-and-animations.html#animation-frames)
- E4 Replay/network：2 processでstate hashを比較し、delay/loss/reconnectとversion差を注入。toyの同一結果からnetwork/engine決定性を推定しない。[Godot high-level multiplayer](https://docs.godotengine.org/en/stable/tutorials/networking/high_level_multiplayer.html)

## 再現・Evidence・Skill

通常検証は読み取りのみです。

```sh
node verify.mjs
node check.mjs
```

新しい原本記録だけ `node verify.mjs --record observations/NEW-ID` と `node check.mjs --record observations/NEW-CHECK`。既存directoryはEEXISTで拒否します。BrowserはUIで操作し、rawをそのまま保存・screenshot取得し、実行環境とSource digestを保持します。checkに別原本を渡す場合は `--node observations/NEW-ID/raw.json --browser observations/NEW-BROWSER/raw.json`。実行やtimestampを既存結果へ後付けしません。

[検証記録](VERIFICATION.md)・[ルーティングSkill](skills/atlas-game-engine-interactive-simulation/SKILL.md)。Sourceは独自実装、図はコードから生成、外部素材・engine codeコピー・新規依存なし。一次資料は設計比較の根拠であり今回実行したengineではありません。全体GoalやSubjectの完成を主張しません。
