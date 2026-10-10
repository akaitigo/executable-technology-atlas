# pulseとsample窓：境界とerasureを分ける

元[Telecom BPSK/pilot](../../../subjects/telecom-sdr/README.md)と[未教材coverageと次実験](../../../subjects/telecom-sdr/README.md#subject主要未教材coverage)のpulse-timing次案を有限8条件へ深掘りします。既知symbolの位相補正→本unitの固定pulseとsample窓→[CRCの検出限界](../../information-theory-coding/crc-undetected-errors/README.md)の順に読みます。CRC passは原文一致を保証せず、erasureの推測やtiming回復を代行しません。旧教材のI>=0規則を変更せず、本unitでは平均0をerasureに固定します。

## 予想→操作→比較→原典→答え

前提はBPSK bit0→+1 / bit1→−1、sample index、有理数、線形和。既存Python stdlib/Fractionのみです。

~~~sh
python3 -B server.py
~~~

動的127.0.0.1 URLを開き、所有serverだけCtrl+Cで終了します。窓処理・平均0の個数・最後の平均を予想し、条件とsample offset 0/1を選んで実行。sample列、各窓indexと値、convolution/paddingの由来、Fraction平均、bit/erasureを比較し、原典・実装・原票を読んで答えを開きます。予想3項目とoffset変更は値を保持して旧答え本文を空にし閉じます。条件変更は予想をunknown・offsetを0へ戻します。実行開始、実行失敗、遅着旧応答も旧比較を使用しません。

## 実行前に固定した条件

[fixtures](fixtures.json)、[手計算表](hand-oracle.json)をproducer実行前に固定。impulse x=[1,0,−1,0,1]、symbol間隔2、窓幅2です。y[n]=Σ x[i]h[n−i]の全supportを実Pythonで求めます。indexは0始まり。窓はoffset+2kとoffset+2k+1（k=0,1,2）。

| pulse / offset | 実convolution sample列 | 窓平均 | 境界・判定 |
| --- | --- | --- | --- |
| [1,1] / 0 | [1,1,−1,−1,1,1] | [1,−1,1] | [0,1,0] |
| [1,1] / 1 | 同上 | [0,0,1/2] | sample6の明示zero-paddingあり、[erasure,erasure,0] |
| [1,1] / 1 paddingなし | 実行前に拒否 | 未計算 | sample6不足、convolution_started=false |
| [1,1,2] / 0 | [1,1,1,−1,−1,1,2] | [1,0,0] | [0,erasure,erasure] |
| [1,1,2] / 1 | 同上 | [1,−1,3/2] | sample6=2は実出力、[0,1,0] |

paddingはsupport外の宣言済み数学的0です。欠落した実測値・欠損packetを0とみなしません。paddingなしの不足窓は計算開始前に拒否し、erasureとも実行障害とも別statusです。longのaligned窓はtail index6を使わず、offset1は使います。故障版bad-zero-bitだけ平均0をbit0に丸め、alignedでBAD_ACCEPTED、offset1は故障非発火FAULT_CONTROLとなります。元bit[0,1,0]はharnessの既知情報で、受信器が未知データを知る証拠ではありません。

## 再現と独立検査

~~~sh
python3 -B runner.py --record
python3 -B check.py
python3 -B route.py pulse-window-symbol-timing
python3 -B route.py unsupported
~~~

--recordだけ新しいUTC folderを作り、既存原票を書き換えません。checker/routeはread-only。[oracle](oracle.py)はproducerをimportせず、先に記した3symbol別のshift寄与ベクトルを列和し、固定sample/index/平均/判定表と整数cross-productで照合。checkerは全積traceとFraction既約表記・由来も検査します。固定8条件：strict窓処理5、期待窓不足1、故障反例1、故障非発火1。6mutantを拒否。rawにはUTC、runtime、fixture、offset、source SHA、全product/窓を残します。

[observations](observations/verification.json)が実IAB、全controlのreset、合成return/HTTP503失敗、実旧応答の遅着破棄、所有tab/server終了、read-only照合をまとめます。sandboxの実bind失敗は保存し、同じlocalhost serverをhost permissionで実行しました。合成QA失敗は実producer障害とは扱いません。captureはtoolで実表示、保存ファイルなしです。

## 原典と範囲

2026-10-05にMIT6.450 Fall2006の[Ch4 §4.1、冊子pp87–89 / PDF1–3](https://ocw.mit.edu/courses/6-450-principles-of-digital-communications-i-fall-2006/d702e3dc1111be9aecf74c2ca711d934_book_4.pdf#page=1)でwaveformとsequenceの関係、[Ch5 introduction/§5.1、冊子pp141–143 / PDF1–3](https://ocw.mit.edu/courses/6-450-principles-of-digital-communications-i-fall-2006/90bcfef40894c3a17214902ff29c3d98_book_5.pdf#page=1)でsignal space・vector加算・linear combinationを確認。例、pulse、窓、erasure契約は独自制作。第三者本文/図の転載なし。原典をこの平均filterの最適性証明として引用しません。

未教材：未知offsetのtiming recovery/PLL、fractional offset、matched filter最適性、AWGN/統計BER、周波数offset、実RF/SDR/ADC、他pulse/長い列、多browser/学習者評価。次案は長いpulseでsymbol別寄与を窓ごとに分解する、fractional offset用の補間規則を先に固定する、別fixtureでnoiseとerasureを分離する、CRCへ渡すbit/erasure契約を定める。いずれも未制作です。module-local Skill routingは同一agent検査で独立Forward Evalではありません。入口追加0、Subject/Atlas incomplete。Core/fullGate、commit/push/publication/install/settingsは対象外です。
