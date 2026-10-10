# Media / codec / streaming — bytes・時刻・到着・再生を分ける

このrepoから対象分野を学ぶ入口。今回の有限1教材は**実mono16 PCM WAV bytesの生成/読取**と**固定arrival列のjitter buffer模型**。H264/AAC等の製品圧縮codec・実ネットワーク・実配信・実playback timingは未実行。

## 学習の道筋

1. **前提**：signed整数、little endian、sample/frame/channel、byte、ms、packet、sequence。monoでは1frame=1sampleだが、byteやmsと同じではない。
2. **主要概念・仕組み**：PCM→WAV header/data、sample clock→chunk PTS、arrivalと提示deadline、buffer、underflow/late drop、startup delay。codec、container、transport、playoutは別の層。
3. **今回実装・正常異常**：[信号/timeline UI](index.html)で予想→操作→比較。[media.py](media.py)と[独立oracle](verify.py)を読む。実WAV bytesと模型traceを別に見る。
4. **実務判断**：到着順ではmedia順を保証できない。遅延を増やすと欠落を減らせても、packet lossや並び誤りは自動で直らない。形式名だけでなくheaderと読めたdata長を検査する。
5. **限界**：4packet、整数ms、固定arrival、mono16/8kHz、固定delay、欠落はzero fill。圧縮・実protocol・adaptive jitter estimator・device clock・主観音質は測らない。
6. **原典→次の学び**：[locator](sources.json)と[coverage](coverage.json)からtimebase drift、capacity/adaptation、RIFF chunk拡張、concealmentの4実験へ進む。

## 予想→操作→比較→原典/実装→答え

予想：packetが全部来ればarrival順で正しい音声に戻るか。deadline後のpacketを今のslotへ入れてよいか。buffer delayを増やせばlossも回復するか。wave.readframesが返っただけで宣言した全frameを読めたと言えるか。

module directoryでMac直接Python stdlibのみ。

```sh
python3 verify.py
python3 serve.py --port 0
# startupに表示した実際のHTTP127.0.0.1 URLを開く。終了Ctrl-C。
python3 route.py wav
python3 route.py h264
```

操作：[UI](index.html)でcase・PTS/arrival-order・delay0/10/30msを選び、4slotのdeadline/arrivals/buffer/提示seqを再生する。source信号と出力を比較し、[実WAV](observations/source.wav)のheader/bytesを読む。図の時間は固定模型のrelative msで、実配信計測値ではない。

### 実bytesの観測

mono・signed16 little endian・8000Hz・320frames。block_align=1×16/8=2bytes、byte_rate=8000×2=16000bytes/s、data=320×2=640bytes、duration=320/8000=40ms、classic44byte header込み684bytes。chunk80frames=10ms、4chunkのPTSは0/10/20/30ms。source samplesは8sample固定patternを繰返し、chunkごとに1000を加えて順序差が分かるようにした。

Python `wave` で実WAVを作りreadbackし、独立RIFF chunk/header parserと `int.from_bytes(signed=True)` でheader/sampleを照合。UIもsource.wavをHTTP取得し、この固定classic headerとPCMをbytesから表示する。圧縮率や圧縮codec実装の検証ではない。

未知format tag3はこのPython/decoderで拒否。mono8bit PCMは有効なWAVだが本教材の対応範囲外で拒否する。dataを2byte短くしたWAVはreadframesの返却長を検査し拒否。signed16の-32768/32767は実bytesでroundtrip、範囲外/boolはencode前に拒否。

### 固定timelineの比較

各slot iの提示deadlineはdelay+10i ms。arrival≤deadlineのpacketを先に処理する（等号を含む）。PTS方針はseq=iだけ提示し、deadlineを過ぎた旧seqをdrop。arrival-orderは最初に来た未提示packetを出す意図的naive。欠落slotは80samplesのzero fill、cadenceを止めずに次slotへ進む。delayは初期待機で、各packetのbuffer滞在時間や総通信遅延と同じではない。

|case|固定arrival（seq0/1/2/3 ms）|読み取れること|
|---|---|---|
|ordered|0/10/20/30|deadline等号でも提示可、全delayで正常|
|reordered|0/25/22/30|PTS delay0は[0,欠,欠,3]、delay10は[0,欠,2,3]、delay30は[0,1,2,3]。arrival-order delay30は[0,2,1,3]で欠落なしでも並び誤り|
|late-first|15/10/20/30|first packet遅延とseq順の逆転を区別|
|loss|0/10/欠/30|待ってもseq2は来ない。arrival-orderではseq3をslot2に出す場合もある|
|burst|30/30/30/30|固定tieはinput順。delay30なら全packet待機、delay0は3slot欠落|
|just-after-deadline|0/11/20/30|1ms遅れでもdelay0のslot1はunderflow。delay10で救える|

reorderedケースの比較用3出力samplesも実WAVへ包装してreadbackする。reorderedのPTS delay30はsource.wavとbyte一致、arrival-order delay30は同じ長さでもsample順とhashが異なる。PTS delay0はzero fillを含む。ここで確かめるのは固定列のsample一致とdeadline判断で、実音質・ネットワーク性能・OSの再生時刻ではない。

原典/実装：[Python3.9 wave](https://docs.python.org/3.9/library/wave.html)のreadframes/writeframes、[RIFF](https://learn.microsoft.com/en-us/windows/win32/xaudio2/resource-interchange-file-format--riff-)のchunk、[WAVEFORMATEX](https://learn.microsoft.com/en-us/windows/win32/api/mmeapi/ns-mmeapi-waveformatex)のblock align/byte rateを実headerへ対応させる。[RFC3550 §5.1/6.4.1](https://www.rfc-editor.org/rfc/rfc3550.html)でsample timestampと到着時刻を区別し、模型のtimelineへ戻る。模型はRTP/RTCP準拠実装ではない。[WebCodecs](https://www.w3.org/TR/webcodecs/)と[HLS RFC8216](https://www.rfc-editor.org/rfc/rfc8216.html)は圧縮pipeline/配信へ進む入口で、今回は実行していない。

答え：全packetがあってもarrival順はPTS順ではない。遅延待機はdeadline内に来るpacketを増やすが、失われたpacketや誤った並べ方を直す根拠にはならない。zero fillは模型の欠落処理で品質保証ではない。WAVは宣言値だけでなく実data長・sample・format対応範囲を確認する。

## Subject主要未教材coverage

[具体的な概念・問い・次実験](coverage.json)と[公式locator](sources.json)を対応させる。

|領域|次に学ぶ概念・問い|今回|
|---|---|---|
|信号/PCM|channel、bit depth、resampling、aliasing。sample/byte/時間を区別できるか|mono16のみ|
|圧縮codec|lossy/lossless、quantization/prediction、H264/HEVC/AV1、AAC/Opus、quality/bitrate。PCM包装と何が違うか|未教材|
|container|MP4/WebM、track/metadata、mux/demux、interleaving/seek。codecとmetadataを分けるか|classicWAVのみ|
|timestamp/sync|PTS/DTS、timebase、A/V sync、clock drift、discontinuity。到着順と提示時刻は同じか|固定msのみ|
|transport|RTP/RTCP、loss/reorder、congestion、retransmit/FEC。未到着と並び誤りは別か|固定入力のみ|
|buffer/latency/PLC|adaptive delay、capacity、deadline、concealment。待機は何を救えるか|固定delay/zero fill|
|streaming|HLS/DASH、manifest/segment、ABR、CDN/cache、live/VOD。decodeと配信はどこで分かれるか|未教材|
|playback/device|queues、render scheduling、hardware/device clock、backpressure、lifecycle。実提示時刻は測れたか|未教材|
|品質/運用|bitrate、QoE、主観品質、latency distribution、failure trace。sample一致で十分か|byte/有限traceのみ|
|delivery security|key/IV、DRM、origin/CORS、privacy/integrity。正しさと権限を別検査できるか|未教材|

次の4実験（未実施）：①有理数timebase/clock driftで丸め・累積同期ずれを手計算比較（[RFC3550](https://www.rfc-editor.org/rfc/rfc3550.html)）。②固定burstにcapacity/簡単なdelay適応を加え、overflow/underflow/待機を別metricで比較（同RFC）。③RIFFのJUNK/odd length/padding/不正長を独立offset oracleで比較（[RIFF](https://learn.microsoft.com/en-us/windows/win32/xaudio2/resource-interchange-file-format--riff-)）。④PCM欠落に前chunk反復/補間を加え波形/MSEを独立算術比較し、主観音質とは区別（[PCM](https://learn.microsoft.com/en-us/windows/win32/api/mmeapi/ns-mmeapi-waveformatex)）。

## 証拠・検査

[audio](audio.json)、[arrivals](fixtures.json)、[手書きheader/timeline](oracle.json)、[raw](observations/raw.json)、[receipt](observations/receipt.json)。実WAV/byte反例、UTC実行時刻、Python/OS/architecture、input/raw/source/artifact SHA-256を結合。hashは同bytesの識別で、品質/実配信の保証ではない。

通常 `python3 verify.py` はread-only、原票更新だけ明示 `python3 verify.py --record`。独立manual RIFF/sample parserと手動36timeline・別deadline/rank oracle、100固定seed timeline×2方針を照合。format/sample/chunk/packet/option拒否22件、WAV拒否4件、sample符号境界を検査。rawに全random input/expected/resultを保存。[Skill](skills/atlas-media-codec-streaming/SKILL.md)は既存runner/checker/UIへ限定routeし、作者smokeを独立AgentEvalと呼ばない。

[実IAB QA](observations/ui-qa.json)と[検証記録](VERIFICATION.md)はcapture取得/保存可否とownedresource終了を区別する。有限1単位で全Subject/Atlas完成を主張しない。
