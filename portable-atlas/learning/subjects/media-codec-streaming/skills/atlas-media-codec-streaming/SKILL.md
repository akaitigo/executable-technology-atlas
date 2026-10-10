---
name: atlas-media-codec-streaming
description: 実mono16 PCM WAV bytesと固定arrivalの有限jitter buffer模型を再現し、PTS順・到着順・underflow・startup delayを既存checker/UIで比較する。製品圧縮codecや実ネットワーク配信は未対応。
---

# PCM bytesと有限bufferへの限定route

[README](../../README.md)、[信号/timeline UI](../../index.html)、[既存実装](../../media.py)、[独立checker](../../verify.py)へroute。実WAV観測と模型arrivalを区別する。

module directoryで `python3 verify.py` はread-only。[raw](../../observations/raw.json)と[receipt](../../observations/receipt.json)のinput/source/artifact hashを確認。[source WAV](../../observations/source.wav)は実bytes。原票更新を明示要求された場合だけ `python3 verify.py --record`。一時HTTPは既存 `python3 serve.py --port 0` の実startup URLをIABで開き、所有tab/serverを閉じる。

`python3 route.py wav` は対応。pcm/wav/pts/jitter-buffer/underflow/startup-delay/traceのみ。`python3 route.py h264` 等は未対応とし[coverage](../../coverage.json)を案内する。作者routing smokeで、独立AgentEvalではない。

mono16/8000Hz、320frames、640PCM bytes＋44header、40ms、4chunk×10ms。reorderedのPTS delay30はsourceとbyte一致、arrival-orderは[0,2,1,3]で並び違い。delay0の欠落はzero fill。lossは待機でも復元できない。未知format/短いPCM/本教材外PCM8bitを区別し、圧縮codec・RTP/HLS実装・実音質/再生時刻の検証へ拡張しない。[公式locator](../../sources.json)と次教材を案内する。
