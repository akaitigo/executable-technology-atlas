# RIFF/WAVのチャンク長とパディング — 3-byte JUNKの次offset

[元media教材のcontainer-chunks候補](../../../subjects/media-codec-streaming/coverage.json)を実bytesで進める独立continuation。codec samplesとcontainer traversalを分け、元Subject/他教材は凍結したまま。

## 読む順番

1. [元media教材の実PCM/WAV観測](../../../subjects/media-codec-streaming/README.md)でsample/frame/byte、signed16とlittle endianを確認する。本単元ではjitter/到着時刻を扱わずcontainer bytesへ進む。
2. [手書きoffset/PCM表](oracle.json)を読み、chunkSizeと8-byte header/padを分けて次offsetを予測する。
3. [実parserとwave比較](worker.py)、[独立checker](checker.py)、保存rawを順に照合し、UIで正常JUNK→pad省略→短dataを操作する。
4. 下の実務判断へ進み、宣言長・実返却長・対応formatの境界を説明する。次の未実験は[coverage](COVERAGE.md)へ。

## 前提 → 予測 → 操作 → 比較

前提はbyte offset、little endian uint32、半開区間、signed mono16 PCM。固定samplesは1000,-1000,32767、期待PCM hexはe80318fcff7f。classicRIFF/WAVE、fmt payload16 bytes、mono16/8000Hzのみ。

python3 preview.py の専用動的loopback URLを開く。fixture、strict／pad省略故障版、chunkを選び、次offsetとparser全体の受理／拒否を予測。「観測と比較」でheader/payload/padの図、宣言／実長、PCM、wave実readを比較する。条件変更は予測もclear、予測変更は前の結果／答えだけclearする。入力拒否も予測と対照できる。

[手書きoracle](oracle.json)は実行前に固定した。fmt header12→payload20..36。odd JUNK header36、payload44..47（宣言3）、pad47..48（1）、次data header48、PCM56..62。JUNKを挿入してもPCMは同じ。even JUNK4ではpayload44..48、pad0、次48。chunkSizeはpadと8-byte headerを含まない。

故障版はodd JUNKのpadを飛ばさず次47。headerを00 64 61 74として誤読し、declaredSize1633、dataEnd1688となって境界拒否。正常JUNKの3-byte payloadがaudio sampleへ混ざったわけではなく、traversalの誤り。

## 独自strict契約とwave実挙動

|fixture|実bytes / RIFF end|strict教材parser|
|---|---|---|
|base|50 / 50|受理、3samples|
|odd-junk / even-junk|62 / 62|受理、同じ3samples|
|RIFF宣言oversize|62 / 1008|riff-length-mismatch拒否|
|data宣言10・実6|62 / 62|chunk-payload-bounds拒否|
|data宣言6・実4|60 / 60|chunk-payload-bounds拒否|
|odd JUNK pad欠落|61 / 61|次header誤読、境界拒否|

strict正常3、契約拒否4。受理契約は正確なRIFF全長、完全なchunk header/data/pad、fmt16/PCM mono16、単一data、frame alignment。これをwaveの仕様や全RIFF規格への適合判断と同一視しない。

各fixtureを実Python wave.open/readframesで読み、status/read/exception、宣言frame数、要求frame数、返却bytes、PCM、全宣言frame取得boolを保存する。**waveが実際に拒否した場合と短readを返した場合をそのまま保持する。** strict拒否でもwaveが読める場合をstrict成功へ数えない。特に短dataは返却長が宣言frame bytesと一致するかを別検査する。実挙動はCURRENTのrawとQAを読む。

## bounded実装と証拠

- fixtureは最大62 bytes、workerは最大1025 bytesだけ読み込み1024超を拒否、readframesは最大16frames。宣言長に応じた領域確保をしない。図も実file範囲へclip。巨大な数値は比較と表示だけに使う。これを任意mediaへのsecurity保証とはしない。
- [worker](worker.py)、[runner](runner.py)、[独立checker](checker.py)。checkerはproducerをimportせず独立literal hex/offset/PCM表で検査。waveは別に直接read/exceptionを再観測して保存値と一致するかを確認する。
- [CURRENT](CURRENT)のrunに実input.wav、worker/oracle copy、command/input/UTC/exit/stdout/stderr、strict/fault trace、wave read、result/stdout、artifacts.jsonのbytes/SHA256。runtime Python/OSを記録。
- python3 runner.py / checker.py / route.py inspect はread-only。明示新規観測だけ python3 runner.py --record / route.py record。UTC別runへ追記して旧rawを保持。
- python3 test_negative.py はraw/derived/hash整合済み6改変を一時copyで拒否し、通常経路の全file SHA256/mtime_ns不変を確認。
- [QA](QA.json)、[coverage](COVERAGE.md)、[module Skill](skills/riff-chunk-padding/SKILL.md)。route lessonはUI位置、未知routeはexit2。個人絶対pathは保存せずsubprocess runtime pathだけ名前へ正規化。

## 原典と実務判断

[Microsoft RIFF: chunkID/chunkSize/data](https://learn.microsoft.com/en-us/windows/win32/xaudio2/resource-interchange-file-format--riff-)のWORD boundary paddingと、chunkSizeにpadding/headerを含めない説明を確認した。[Python wave readframes](https://docs.python.org/3.9/library/wave.html#wave.Wave_read.readframes)は要求frame数を「最大」として読むAPI。実返却長も検査する。

元教材のPCM/frame/sampleとjitter模型から、未知chunk/pad/宣言境界のcontainer処理へ増分。RF64、fmt拡張、圧縮codec、再生品質、配信、汎用format保証は未実行。Subject/Atlas全体のcompleteではない。
