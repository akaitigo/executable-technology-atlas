---
name: bounded-watermark-window-finalization
description: この有限2partition教材でglobal minとmax故障、半開窓のfire・late保持・finalizeを実Pythonで比較する。
---

# 限定route

module内で python3 -B route.py inspect / lesson。明示再観測のみ record。previewのloopback URLで予想→実処理→raw/実装→答え。

partition p0/p1、time/value整数0..100、event数1..12、L/A整数0..20。窓[start,end)、到着前WM受理、到着後WM>=end+Aでfinal。未知partition/idle-autoや不正型は拒否、JSON失敗/audit失敗/HTTP/旧応答を正常窓に混ぜない。新UTC原票で旧証拠保持。

元outboxを重複編集せず、このmoduleだけ。実Flink/idle自動判定/無限stream/production保証や全Subject完成を主張しない。README/COVERAGEを読む。install/公開/共有設定は対象外。
