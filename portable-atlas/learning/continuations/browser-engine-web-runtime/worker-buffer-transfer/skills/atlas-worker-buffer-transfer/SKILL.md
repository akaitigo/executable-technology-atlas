---
name: atlas-worker-buffer-transfer
description: 実Dedicated Workerの固定4bytes clone/transferと関数拒否をID/ack/件数で検証する。速度、zero-copy、process、共有memory、安全性保証には使わない。
---

rootは ../..。READMEで固定3fixtureと所有状態の事前表を読む。正常2と期待DataCloneError1を分け、timeoutを未到達の証拠にしない。

rootで `python3 -B skills/atlas-worker-buffer-transfer/route.py worker-buffer` は保存rawをread-only検証。新実行は `server.py` のIAB UI、明示「新原票を保存」だけfresh UTC採取。通常check/routeは原票を変更しない。

sender直後/ack後bytes、worker sum/change、前後probe ID/件数、例外、終了を確認する。関数拒否では後続probe ackでID一覧空を確認する。速度・物理zero-copy・OS process・SAB/Atomics/SW・sandbox等は未対応としてREADME境界/次案へ戻す。
