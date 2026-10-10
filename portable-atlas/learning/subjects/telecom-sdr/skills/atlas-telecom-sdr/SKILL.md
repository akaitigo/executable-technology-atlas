---
name: atlas-telecom-sdr
description: 有限BPSK complex baseband、固定noise/quadrant位相、known pilot補正とBERを既存checker/constellation UIへ限定routeする。実RF送受信・SDR機器・通信規格適合は未対応。
---

# finite BPSKへ限定route

[README](../../README.md)、[UI](../../index.html)、[既存BPSK](../../bpsk.py)、[独立checker](../../verify.py)を読む。計算I/Qとdevice/RF captureを混同しない。

module directoryで `python3 verify.py` はread-only。[raw](../../observations/raw.json)と[receipt](../../observations/receipt.json)のinput/source/artifact hashを確認。[complex samples](../../observations/complex-samples.json)は計算pair、device formatではない。原票更新を明示要求された場合だけ `python3 verify.py --record`。IABは既存 `python3 serve.py --port 0` の実startup HTTP URL、所有tab/serverを終了する。

`python3 route.py bpsk` は正常。bpsk/iq/phase/pilot/ber/fixed-noise/traceのみ。`python3 route.py rf-transmit` 等は未対応で[coverage](../../coverage.json)へ。作者routing smokeは独立AgentEvalではない。

0:+1/1:-1、symbol hold4samples、exactquadrant、I=0→bit0を明示。90°noneは8/16、正常pilotで0/16。strong noiseは3/16残り、biased pilotは16/16、pilot相関0はNO_PHASE_ESTIMATE/BERNone/比較0bit。BER分母はpayload16でpilot除外。統計AWGN性能/実通信・規格保証へ拡張せず、[一次locator](../../sources.json)とphase drift/pilot品質/pulse timing/noise統計の次教材へ案内する。
