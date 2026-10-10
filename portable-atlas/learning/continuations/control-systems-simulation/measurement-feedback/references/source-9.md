# 平均が目標ぴったりでも、noiseで揺れる

[QE別章](../../../quality-engineering-atlas/COVERAGE.md)の制御×noise全因子・平均分散tradeoff・確認runの入口を専有unitで制作。制御C0/C1、noise N-/N+、各cell3整数の架空合成表です。実物noise試験・Taguchi全体系の完了ではありません。旧DOE/Wilson/SQLite/QE/global/Coreは変更しません。

## 先に固定する目的・loss・fixture

nominal目標10 arb、lossは1係数の平均二乗偏差 `mean((y−10)²)` arb²。noise2水準を等重み1/2、各setting6観測に集計。これは宣言した教材の損失で、金額やNISTが推奨する許容値ではありません。別fixtureの選択setting loss≤3を確認成功とし、条件を後付け変更しません。

| 選択fixture | 平均 | V（分母6） | s²（分母5） | 目標loss | noise平均差 |
|---|---|---|---|---|---|
| C0: [6,7,8] / [12,13,14] | 10 | 29/3 | 58/5 | 29/3 | 6 |
| C1: [10,11,12] / [10,11,12] | 11 | 2/3 | 4/5 | 5/3 | 0 |

平均だけならC0を好んでも、目標lossではC1を選択。低ばらつきC1の平均を15へずらす例ではloss77/3となりC0を選ぶ。分散だけ最小化しても目標loss最小にはなりません。

選択後settingを固定。別ID/別全配列の確認pass fixtureでC1は[9,10,11]/[11,12,13]、mean11/V5/3/loss8/3で基準≤3を満たす。失敗fixtureは[13,14,15]/[15,16,17]、mean15/V5/3/loss80/3で失敗。確認側でC0が良くてもC1を選び直さず、失敗のまま残す。tie例は選択loss2/3が同じためunique choiceなし、確認未実行。perfect-targetはloss0/V0を有限0として扱います。SNや無限値に置換しません。

[手表](hand-oracle.json)/[時刻とSHA](qa/oracle-before-producer.json)はproducer作成前に固定。選択用と確認用は別の authored synthetic fixtures です。IDと全配列が異なることは統計独立性の実証ではありません。同IDと全配列コピーは教材のreplay防止契約で拒否します。独立な実標本が偶然同値となることを否定する一般規則ではありません。個々の観測値の重複は許容。

## 予想 → 操作 → tradeoff/確認 → 原典/原票 → 答え

[画面](index.html)で例/予想を選び、実入力の選択→別fixture確認を実行。JSONを編集するとPython childへPOSTして再計算します。選択と確認を分けた2図、目標破線、noise別平均/架空反復点、平均/V/s²/loss/感度の表を比較。太線は選択固定settingで、確認側の値でwinnerを変えません。tieは確認図なし。入力拒否は選択/確認/答えなし。

例/予想/JSON/明示resetで旧図・表・原票・答えを空にして全detailsを閉じ、変更後値を保持。resetは選択例へ戻し予想を空にする。古い遅延応答を表示しません。通信/child失敗は正常答えを作りません。

```sh
python3 -B checker.py
python3 -B runner.py
python3 -B qa/check-ui.py
# 明示採取だけ新UTC固定原票
python3 -B runner.py --record
# memory-only / default delay0 / dynamic loopback
python3 -B server.py
# stale応答QA専用人工遅延
python3 -B server.py --delay-ms 600
```

既存Mac標準libのみ。server起動/GET/POST/exportはunitのSHA/mtimeを変えない。生存中RAM原票は固定HTML viewer `/view/receipt/{id}` とJSON `/receipts/{id}.json`、readonly export `/api/receipts`。512件までRAM保持し停止で失効。QA採取だけ明示snapshotを専有dirへ保存。新serverは新原票で再試験し、過去RAMを復元/上書きしません。README/source/Skill/元QEは固定allowlistのescaped text viewerで表示し、親ファイルを編集しません。記録専用serverではありません。所有serverはCtrl-C、保護port53478/60285/50835や他ownerは操作しない。install/課金/公開/commit/pushなし。

## 分母と独立oracle

[producer](calculate.py)はFractionで偏差平方を直接集計。pool Vの分母6、unbiased sample s²の分母5、cell内s²の分母2を区別。`loss = bias²+V` であり、bias²+s²ではありません。Vは等noiseのcell内population成分とcell平均間成分に分解。合成finite表の分解で、未知母集団の分散や真のexpected lossの推定保証ではありません。

[checker](checker.py)はproducerをimportせず、pairwise差の平方からVとs²、2次moment `E(y²)−20E(y)+100` からtarget lossを検算。選択fixtureだけのunique最小lossからwinnerを決め、別fixtureで同winnerのlossを照合。手表5例、分母取り違え/平均だけ選択/確認再選択/同data確認/偏りを平方しない/noise成分消去/単位平方/tie任意選択/zero loss無限化/統計独立/SN偽称の12mutantを拒否。

[契約](contracts.json)はunit arb/target整数10/loss_limit整数3、selection/confirmationにidと4cell各3整数−20..40。bool/float/NaN/Infinity、duplicate/unknown keys、任意path、同ID/同全配列は拒否。未知targetやloss基準、noise重み/反復数、他単位は別契約が必要です。

## 因子の違いと未教材

制御factorは設計者が選ぶsetting、noiseは製造/使用時に制御しにくい変動（実験では意図的に条件を与える）、signalは利用者の意図を伝える入力、adjustmentは平均調整の概念。今回は目標固定でsignalを変えず、adjustment操作も実装しません。parameter designはnoiseに対しsettingを選ぶ設計段階、tolerance designは許容差と費用を検討する別課題。後者は未教材。

[NIST Taguchi §5.5.6](https://www.itl.nist.gov/div898/handbook/pri/section5/pri56.htm) Parameter Design/平均とばらつきtradeoffを入口に、[NIST Robust Designs](https://www.nist.gov/document/robdesgn-1pdf) p5 Classification/p20 Analysisをfactor区別と別要約へ、[NISTIR6524](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nistir6524.pdf)印刷p23のquadratic lossを損失の分解へ結ぶ。今回の閾値/合成値/等noise重みは我々の有限契約で、原典の実測値は流用しません。

SN比は採用せず、式/zero/undefined扱いは未教材。SNがrobust設計全体ではありません。直交表/aliasing・dynamic signal-response・確認の統計独立性・実物noise耐性・無作為化/反復実施・因果/有意性/検出力・費用/実データは未実施。合成noise2条件の基準を満たしても、一般環境でrobustとは保証しません。[sources](sources.json)/[COVERAGE](COVERAGE.md)/[Skill](skills/atlas-control-noise-robustness-confirmation/SKILL.md)/[QA](qa/README.md)へ。中央受入待ちで、全分野完成/旧QE受入数への加算/統合approval迂回は宣言しません。
