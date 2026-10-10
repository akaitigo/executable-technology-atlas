# main effectがゼロでも、Aの効き方は反転する

[QE coverage④](../../../quality-engineering-atlas/COVERAGE.md)の「反復2因子実験」を、この専有unitだけに教材化します。4cell×各3個の架空整数応答でmain effect・interaction・within-cellばらつき・OFATの欠測を比較。旧unit/QE/Subject/Portal/global/Coreは変更しません。中央受入待ちの有限教材で、全分野完成ではありません。

## 先に固定した手計算

cell順はA-B-,A+B-,A-B+,A+B+。各cellの反復値は平均±1と平均、wide-noiseだけ±3。単位は架空arb。r=3、N=12。

| 合成例 | cell平均 | main A / B | AB effect | 条件A B- / B+ | 差の差 | cell内MSE |
|---|---|---|---|---|---|---|
| additive | 10,14,12,16 | 4 / 2 | 0 | 4 / 4 | 0 | 1 |
| interaction | 10,12,12,22 | 6 / 6 | 4 | 2 / 10 | 8 | 1 |
| crossover | 14,6,6,14 | 0 / 0 | 8 | −8 / +8 | 16 | 1 |
| wide-noise | 10,12,12,22 | 6 / 6 | 4 | 2 / 10 | 8 | 9 |
| flat | 10,10,10,10 | 0 / 0 | 0 | 0 / 0 | 0 | 1 |

[手表](hand-oracle.json)はproducer作成前に固定し、[時刻・SHA](qa/oracle-before-producer.json)を保存。±1反復のcell内平方和は2×4=8、残差df=12−rank4=8、MSE=1。±3ではSSE=18×4=72、MSE=9。response/effect/係数はarb、SS/MSEはarb²。同じinteraction平均でもcell内ばらつきは別です。crossoverはA効果の符号反転で定義し、主効果ゼロを必要条件にしません。

## 予想 → 操作 → 正常/異常図 → 一次資料/実装 → 答え

[画面](index.html)で例と形の予想を選び「この実入力を計算して比較」。JSONの合成値を編集すると、実際にPython childへPOSTします。全因子の平均線/反復点と、OFATの未観測cellへの加法予測を比較し、cell内SSE/分散、±1係数/SS/自由度、実stdin/stdout/source SHAのmemory原票を読み、答えを開きます。

crossover例はmain A/B=0でも条件Aが−8/+8。OFATは先頭3cellの投影だけで、第4cellを測りません。加法予測6+6−14=−2、全因子の第4平均14との差16。−2は観測値でも推奨設定でもありません。全因子の参照平均は実線、OFAT予測は点線/菱形で区別。

入力例・予想・JSON変更時と明示resetで旧図/表/trace/答え/linkを消し、開いた全detailsを閉じます。resetは選択例のJSONを戻し予想を空にする。変更後の新値を保持し、古い遅延応答は表示しません。入力拒否exit2は効果/図/正常答えなし、child/通信失敗exit3は別です。

```sh
python3 -B checker.py
python3 -B runner.py
python3 -B qa/check-ui.py
# 初回/明示採取だけ新UTC固定原票を作る
python3 -B runner.py --record
# 起動・GET・POSTでunitファイルを記録しないmemory-only server
python3 -B server.py
# stale-response QA専用の人工遅延
python3 -B server.py --delay-ms 600
```

既存Mac Python標準libのみ。serverはdynamic loopback、起動stdoutのURLへ接続。通常起動はdelay0、rootの再試験でもunit SHA/mtimeが変わりません。新recordだけ固定rawとobservation-data pointerを作り、旧原票を上書きしません。serverは512件までRAM receiptsを保持し、`/receipts/{id}.json`が生存中のJSON原票、`/view/receipt/{id}`がescaped textのHTML表示、`/api/receipts`がread-only export。停止時にRAM原票は消え、UI原票linkも失効します。QAは明示的にsnapshot保存し、その後の読取では保存原票へ戻ります。record-only serverではありません。600msはstale確認用人工遅延で、工程性能の観測ではありません。

所有serverはCtrl-Cで終了。保護port53478/60285/50835や他ownerを操作しません。install/課金/公開/commit/pushなし。

## 規約と独立oracle

`m00,m10,m01,m11`をcell平均とする。effect A=(m10+m11−m00−m01)/2、B=(m01+m11−m00−m10)/2、AB=(m00+m11−m10−m01)/2。条件A差はB-でm10−m00、B+でm11−m01。差の差DODは後者−前者で、2×effectAB。

±1 model `y=beta0+betaA*xA+betaB*xB+betaAB*xA*xB` では各effect=2 beta、DOD=4 betaAB。AB effectという名に他の規約もあるため、ここではこの倍率を固定。main-only modelはABを落とすため、SS_ABが残差へ混入する。SS_A/SS_B/SS_AB各df1、within df8、total df11。平方和は12 beta²とcell内残差へ分解します。F/p-value/有意性は出しません。

[producer](calculate.py)はFractionによるcell平均contrast。[独立checker](checker.py)はproducerをimportせず、12行の±1 model matrixのnormal equationsを有理Gaussian eliminationで解き、rank・run-level残差・列を落としたnested RSS差からSSを検算。OFATは別の0/1符号化3点modelを解き、第4予測を求めます。手表との一致に加え、main-onlyでABを消す、effect/係数倍率、DOD倍率、df=N−1、分散をrで割る、SSEとeffect混同、単位平方抜け、第4cell観測偽称、randomized偽称、crossoverを加法と分類する10mutantを拒否。

[契約](contracts.json)はexact keys unit/cells、unit文字列arb、4cell×3値、bool/floatではない整数−20..40。NaN/Infinity、duplicate/unknown key、欠cell/不均衡反復、別単位/範囲/任意パスは拒否します。固定例以外の有限整数編集も同じ独立OLSで検算します。

## raw・模型・未実施

CLI/HTTPの入力と計算出力は実行原票です。原票の応答値自体は架空合成データで、実測実験ではありません。3値を「合成反復」と呼んでも実物の独立反復は未実施。array順は表示順で、時間順序やrandomizationではありません。scatterの横jitterは重なりを避ける表示だけ。順序・無作為化・独立性・等分散・測定系・実因果・有意性/検出力を実証していません。SSE/MSE=0でもdf8は変わらず、無限F/確実な効果へ置換しません。実データ・個別推奨・Taguchi SN比/直交表は対象外。

[NIST Choosing a Design](https://www.itl.nist.gov/div898/handbook/pri/section3/pri3.htm)を設計目的・因子水準の入口に、[two-level full factorial](https://www.itl.nist.gov/div898/handbook/pri/section3/pri3331.htm)のstandard order/model matrixを±1符号化と反復へ、[How to model DOE data](https://www.itl.nist.gov/div898/handbook/pri/section4/pri43.htm)をmainとinteraction両方のmodelへ結びます。NIST事例の実数値を今回の合成実験へ流用しません。[sources](sources.json)/[COVERAGE](COVERAGE.md)/[有限Skill](skills/atlas-replicated-two-factor-interaction/SKILL.md)/[QA](qa/README.md)で根拠・未教材・実画像・失敗とcleanupを辿れます。固定allowlist `/view/qe-coverage` は元QE文書をread-onlyで提示し、専用rootの親相対404をviewer入口で解消します。原票/README/source/SkillもHTML viewerでescaped textとして表示し、任意パスは受けません。JSON直接表示のブラウザ制約は回避せず、許可されたHTML表示と区別。Portal統合は今回行いません。
