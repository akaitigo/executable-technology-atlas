# 固定seedと失敗保持shrinking

[教材](index.html)は、[元教材の実験1](../../../subjects/software-quality-engineering/LEARNING_PATH.md)を独立した有限模型として実行します。予想を選び、generator・seed・件数・正常版/M1/M2を操作し、生成全入力、最初の反例、縮小候補、局所最終、global最小を読み、最後に答えを開きます。元教材は変更していません。

## 再現

既存Mac Python標準ライブラリだけを使用します。インストール不要です。このdirectoryで実行します。

```sh
python3 -B verify.py
python3 -B route.py
python3 -B serve.py
```

最後のcommandが出す127.0.0.1 URLを開きます。終了はそのprocessにCtrl+C。模型を再実行するUIと、保存CLI原票を読むsource viewerは別です。通常verify/routeは既存原票・receiptを上書きせず、実行意味とhashを照合します。初回記録とsealは制作時専用で、既存記録への再記録は拒否します。単独file URLはAPIを持たないため対応しません。Core/global gate、commit/push、公開、設定変更は今回の範囲外です。

## 固定した入力契約

lo/hiは整数-3..3、lo≤hi、xは整数-4..4、252組です。正常版は半開区間 `[lo,hi)`、M1は下端を除外、M2は上端を含みます。期待値は `range(lo,hi)` の整数集合にxが属するかです。集合Oracleと対象比較式を分け、独立checkerはproductionをimportしません。NaN、浮動小数、JS比較coercion、無限整数全体を扱いません。

configはgenerator=`uniform`/`boundary`、JSON整数seed=1/7、JSON整数count=2/4、variant=`original`/`M1`/`M2` の4keyのみです。bool、`1.0`、余分なkey等を拒否します。ブラウザはJSONの数値lexemeを保って送るため、`2.0`を勝手に整数2へ変換しません。lo>hiの縮小候補はSCHEMA_INVALID、仕様差が消える候補はLOST_FAILUREです。

uniformは独自LCG `state=(5*state+1)%256` のstate 252..255を拒否し、残ったstateを辞書順の252領域indexへ写します。全256周期で各indexが一度現れることを別検査します。短い固定prefixはIID乱択でも、任意seedで境界を必ず引く証拠でもありません。実行するseed1/7・件数2/4では棄却drawは出ず、draw記録には実際のstateだけを残します。boundaryは同じlo/hiを使い、生成index偶数でx=lo、奇数でx=hiです。

| 条件 | 生成の観測 | 局所縮小とglobalの違い |
|---|---|---|
| uniform seed7 count2 M1/M2 | どちらも反例なし | 全列挙ではM1=21、M2=28失敗 |
| boundary seed7 count2 M1 | 最初 `[-3,1,-3]` | 局所 `[-3,0,-3]`、global `[0,1,0]` |
| boundary seed7 count2 M2 | 最初 `[0,2,2]` | 局所 `[0,2,2]`、global `[0,0,0]` |
| boundary seed1 count2 M1 | 反例なし | boundaryでも短い生成は境界差を逃す |
| uniform seed1 count2 M2 | 最初 `[-3,0,0]` | 局所 `[0,0,0]` はglobalと一致 |
| 正常版、全8条件 | 生成失敗なし | 独立全列挙も0/252失敗 |

## 縮小の順序と最小性

候補順は座標lo→hi→x、それぞれ0→0方向へ1step。重複候補を除き、schemaが有効で仕様差が残り、rankが厳密に下がる最初の候補を受理して先頭から再開します。候補ごとの元入力、規則、期待値/実値、schema、受理拒否、roundを保存します。受理によってrankが下がるので有限停止します。停止時は**この候補規則に対して局所最小**です。複数座標を同時に変える候補はないため、x=lo/hiの関係を保ったまま動けず止まる場合があります。

global判定は別に252組を全列挙し、rank `(abs(lo)+abs(hi)+abs(x), abs(lo), abs(hi), abs(x), lo, hi, x)` 順で最初の失敗を選びます。M1のglobal最小 `[0,1,0]`、M2 `[0,0,0]` と局所最終を比較します。最小性はこのrankと有限領域だけの主張です。生成で反例がなければ局所縮小は実行せず、全列挙の反例を「生成・縮小で得た」と表示しません。

## 原典と未対応

[fast-check Properties](https://fast-check.dev/docs/core-blocks/properties/)はgeneratorとpredicateを組み合わせ、入力を破壊しない注意を示します。[Arbitraries](https://fast-check.dev/docs/core-blocks/arbitraries/)は生成とshrinkerの組を説明し、[Parameters](https://fast-check.dev/docs/api/interfaces/Parameters/)はseedやpathによる再現を扱います。本教材はその概念への入口であり、fast-checkを導入・実行していません。LCG、候補順、rank、global証明はlibrary仕様から引用したものではありません。

[COVERAGE.md](COVERAGE.md)に未対応、[VERIFICATION.md](VERIFICATION.md)に実測と制作時の失敗、[手表](hand-oracle.json)に実装前固定値、[原票](observations/attempt-01.json)にUTC・runtime・digest・24実行・refusal・mutants・全256cycleがあります。実ブラウザQAは別原票です。実captureが保存されていない場合はpath/hashをnullとし、端末や模型図をOS画面captureと呼びません。コード・図・文章は独自制作、Apache-2.0です。
