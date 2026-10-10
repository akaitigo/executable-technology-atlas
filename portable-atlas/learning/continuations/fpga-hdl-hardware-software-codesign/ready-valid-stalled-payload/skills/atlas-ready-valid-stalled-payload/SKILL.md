---
name: atlas-ready-valid-stalled-payload
description: 1offerのready/valid stallをPython理想clockedgeで比較する。RTL/FPGA/timing/CDC/実device成功やAXI適合性には使わない。
---
元FPGA counter/coverage次4→本README/ARM IHI0022H A3.1.1/A3.2.1→事前literal tick表→独立closed-form oracleへroute。edge前にcapture、後にstate更新。正常はstall保持、advance故障はstallで+1、ready無視故障はreceiverがvalidだけ捕捉。1offerの退役を全版で揃える。
可変ready/data/validを実Pythonへ送り、actual tick/captureから信号図・逐次prefix・答えを表示する。変更時は本文/trace/wave/stepを空、details閉、新値保持。拒否/host失敗は正常答えなし。revisionでstale破棄。
通常checker/runner/QAは全unit SHA256/mtime不変・tmpなし。明示record fresh原票、旧失敗保持、UTC/env/source hash、実IAB capture、所有preview/tab cleanup後freeze。install/OS設定/旧unit/Core/公開へ広げない。
