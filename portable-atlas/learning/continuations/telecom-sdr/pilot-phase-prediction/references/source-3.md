# Telecom / SDR — I/Q・位相・pilot・誤り数を分ける

このrepoから対象分野を学ぶ入口。今回の有限1教材は**BPSKの実際に計算したcomplex baseband samples**、固定noise、0/90/180/270°位相、既知pilot補正。実電波の送受信・SDR device・GNU Radio・通信規格適合は実行していない。BERはこの有限vectorの誤り割合で、一般の誤り確率ではない。

## 学習の道筋

1. **前提**：bit、signed整数、complex I+jQ、symbol/sample、回転、閾値、誤り数。baseband arrayとRF/device captureは別の証拠。
2. **主要概念・仕組み**：BPSK0→+1/1→−1、4samples/symbolのrectangular hold、channel gain/phase、symbol平均、known pilot相関→逆回転、Iの符号でhard decision。
3. **今回実装・正常異常**：[constellation/waveform UI](index.html)で予想→操作→比較。[bpsk.py](bpsk.py)と[独立oracle](verify.py)を読む。90°の軸ずれ、固定noise、pilot欠損/逆位相、判定tieを比較。
4. **実務判断**：受信点が±1に見えてもbit mapping/位相基準が逆なら全bit反転し得る。known pilotは位相を合わせる手段で、payload noiseや壊れたpilotを万能に直すものではない。推定不能とBER0を混同しない。
5. **限界**：symbol timingは既知、位相は定常quadrant、gain一律、noiseはsymbol中固定。pulse shaping/ISI/周波数偏差/実ADC/PLL/統計AWGN/FECは未実装。
6. **原典→次の学び**：[一次資料locator](sources.json)と[coverage](coverage.json)からphase drift、pilot品質、pulse/timing、noise統計の4実験へ進む。

## 予想→操作→比較→原典/実装→答え

予想：位相90°でもreal部だけ判定してよいか。既知pilotを使えば強いpayload noiseも必ず直るか。pilot相関0をphase0として処理してよいか。90°のreal部が0なら何bitになるか。

module directory、Mac直接Python stdlibだけ。

```sh
python3 verify.py
python3 serve.py --port 0
# 実startup HTTP127.0.0.1 URLを開く。終了Ctrl-C。
python3 route.py bpsk
python3 route.py rf-transmit
```

操作：[UI](index.html)でcaseとnone/pilotを選び、symbol sliderでreceived/decision点、I/Q波形、入力/復調bitと誤り位置を比較。図は計算arrayの再生で、SDRの実測スペクトラムやRF oscilloscopeではない。

### 計算するsignal

16payload bits、4known pilot bits（0/1/0/1）、payload64complex samples＋pilot16samples。symbol_rate=1000symbol/s、4samples/symbolなのでsample_rate=4000sample/s。payload16msは設定rateからの算術で、実sample clock計測ではない。pilotとpayloadは別array、同じ固定channelを仮定する。

BPSK mappingはこの教材の約束0:+1/1:−1。mappingは実装によって異なる。channelはgain×{1,j,−1,−j}のexact quadrant。90°で `cos(90°)` の微小丸めを判定根拠にしない。noiseは固定I/Q pairをsymbolの4samplesに保持し、AWGNではない。

既知pilotの相関 `ĥ = mean(rx_pilot × known_sign)` を求め、非0なら `conj(ĥ)/|ĥ|` でpayloadを逆回転。振幅は正規化しない。exact0はNO_PHASE_ESTIMATEとして復調/BERをNone、compared_bits=0にする。推定不能を0誤りと報告しない。near-zero推定の品質判定は次教材。

symbol平均後にI<0ならbit1、I≥0（**exact tieを含む**）ならbit0。BER分母は16payload bits、pilotは含まない。これを統計BER曲線やEb/N0の性能と呼ばない。

|case|noneの誤り/16|pilotの誤り/16|判断|
|---|---:|---:|---|
|clean-0 / fixed-noise-0|0|0|位相基準が一致、小さい固定noise|
|clean-90 / fixed-noise-90|8|0|90°ずれをknown pilotで補正|
|clean-180|16|0|同じ2点でもbit mappingが反転|
|strong-noise-0|3|3|位相補正はpayloadの閾値越えnoiseを訂正しない|
|decision-tie|8|8|全I=0をbit0とする固定rule|
|zero-pilot-90 / fade-zero|8|推定不能|pilot相関0、None BER・比較0bit|
|biased-pilot-90|8|16|pilotが逆の位相を指し補正が全反転|
|clean-270|8|0|−90°推定は270°と同じquadrant|

[complex samples原票](observations/complex-samples.json)はfixed-noise-90の計算received/corrected/pilot I/Q。device formatや実電波captureではない。[raw](observations/raw.json)は全caseの送信/受信/判定64samples・pilot16samples・symbol平均・factor・bit・誤り位置を保存する。

原典/実装：[MIT OCW6.450 lecture index](https://ocw.mit.edu/courses/6-450-principles-of-digital-communications-i-fall-2006/pages/lecture-notes/) Ch4/5で波形とsignal space、[Ch6](https://ocw.mit.edu/courses/6-450-principles-of-digital-communications-i-fall-2006/resources/book_6/)でchannel/modulation/demodulation、[Ch8](https://ocw.mit.edu/courses/6-450-principles-of-digital-communications-i-fall-2006/resources/book_8/)でdetection/codingを読む。[bpsk.py](bpsk.py)のmapping、average、pilot estimate、rotation、hard decisionを別々に照合する。[GNU Radio Costas Loop](https://wiki.gnuradio.org/index.php/Costas_Loop)は実同期へ進む公式入口だが本文fetch403で未読、今回はGNU Radio/Costas loopを実行していない。

答え：90°でsignalはQ軸にあり、I判定には情報がない（本tie ruleで8/16）。既知で正常なpilotを使えばこの定常位相を戻せるが、強いnoiseは3/16残り、逆位相のpilotは16/16へ悪化する。pilot相関0なら判断根拠がなく推定不能を示す。固定BERと実リンク性能は別の検証が必要。

## Subject主要未教材coverage

[具体的概念/問い/次実験](coverage.json)と[公式locator](sources.json)を対応させる。

|領域|次に学ぶ概念・問い|今回|
|---|---|---|
|信号/IQ/sampling|Nyquist/aliasing、量子化、sample/symbol rate、I/Q convention。数値とRFを区別するか|定常arrayのみ|
|変調/pulse|QPSK/QAM、pulse shaping、matched filter、ISI、spectrum。点と帯域波形は同じか|BPSK/holdのみ|
|channel/noise/link|AWGN、Eb/N0/SNR、fading/multipath、path loss/interference。16bitを確率へ拡大しないか|固定noise/gain|
|同期|phase ambiguity、pilot、frequency/timing、PLL/Costas、drift。pilotが壊れたらどうか|一回位相補正|
|検出/equalization/FEC|soft/LLR、equalizer、coding/interleave。補正後noiseをどう直すか|hard/tieのみ|
|framing/protocol|preamble、frame sync、CRC、scrambler、ARQ/MAC。bitからpacketを見つけられるか|未教材|
|RF/antenna|mixer/LO、ADC/DAC、AGC/filter、antenna、DC/IQ imbalance。実機は何を変えるか|未教材|
|SDR/real-time|GNU Radio/driver、stream/buffer/clock、overrun、calibration。arrayとstreamの失敗は同じか|未教材|
|communication system|OFDM/multiple access、cellular/WLAN、duplex/scheduler/latency。何の規格まで言えるか|未教材|
|測定/規格/運用|BER confidence、EVM/spectral mask、calibration/traceability、RF権限。実測と計算を分けるか|未教材|

次の4実験（未実施）：①固定phase ramp/frequency offsetで一回補正と小さな追従toyを手計算比較（[Ch6](https://ocw.mit.edu/courses/6-450-principles-of-digital-communications-i-fall-2006/resources/book_6/)）。②pilot magnitude/residual閾値による推定拒否をnaiveと比較（[Ch8](https://ocw.mit.edu/courses/6-450-principles-of-digital-communications-i-fall-2006/resources/book_8/)）。③pulse/ISIとsample offsetを独立離散convolutionで比較（[Ch4/5](https://ocw.mit.edu/courses/6-450-principles-of-digital-communications-i-fall-2006/pages/lecture-notes/)）。④明示noise分布/seed/energy正規化のMonte Carloで試行数と信頼区間を独立算術確認、AWGN仮定を先に固定（[Ch7/8](https://ocw.mit.edu/courses/6-450-principles-of-digital-communications-i-fall-2006/pages/lecture-notes/)）。

## 証拠と検査

[base](base.json)、[fixtures](fixtures.json)、[手書きvector/誤り位置](oracle.json)、[raw](observations/raw.json)、[receipt](observations/receipt.json)はUTC実行時刻、Python/OS/architecture、input/raw/source/artifact SHA-256で結合。hashは同bytesの確認で、実通信/規格の保証ではない。

通常 `python3 verify.py` はread-only、原票更新だけ明示 `python3 verify.py --record`。独立oracleはmainのcomplex変調/推定/復調を使わず、FractionのI/Q成分算術・固定軸・手書きbit/誤りvectorを照合。11case×2policy、100固定seed vector×2policyとsamples/symbol比較、invalid18件・nonfinite4件・option3件。NaN/infは拒否を記録し、非標準JSON数値を原票へ保存しない。[Skill](skills/atlas-telecom-sdr/SKILL.md)は既存runner/checker/UIへ限定route。作者smokeを独立AgentEvalと呼ばない。

[実IAB QA](observations/ui-qa.json)、[検証記録](VERIFICATION.md)はcapture取得/保存可否・ownedresource終了を区別する。有限1単位で全Subject/Atlas完成を主張しない。
