---
name: atlas-emulation-device-snapshot
description: 装置状態を含むsnapshotと継続一致を、4条件の保存列から読む。
---

# 問いから継続比較へ

[README](README.md)→[前提](PREREQUISITES.md)→[画面](index.html)の順に案内する。実VMや保存ファイルの操作は行わず、今回の保存結果を読む。

1. 「PCとメモリーが同じなら十分か」には発火直前を開く。cut2のcounter2と故障版0、tick4のREAD、最終memory[0]を順に比較する。
2. 「発火済みの通知も保存するか」には発火済みを開く。counterは同じ0でもpendingだけが違う。tick6後にpendingが一致しても、先に保存したmemoryの差は戻らない。
3. 「初期やACK後で一致したから正しいか」には初期とACK後を比較する。deviceが既定値と一致する条件だけでは欠落を検出できない。[手計算](HAND-CALCULATION.md)の4行表へ戻る。
4. 「ACKと発火が同時ならどちらが優先か」には[契約](CONTRACT.md)の順序を読む。tick6のtimer発火を記録した後ACKし、境界pendingはfalse。物理装置の規則を推定しない。
5. 「装置欄がないJSONを読み込んでよいか」には正常restoreの事前拒否と別schemaの故障比較を分ける。欠落/type/version拒否では更新0。既定値復元を互換性保証と呼ばない。
6. 「QEMUにもこの結果が当てはまるか」には[原典](SOURCES.md)と独自規約を分ける。内部装置状態の保存という概念はつながるが、周期・命令・JSON形式と全結果はこの教材だけ。実QEMU/HVFやlive migrationの実証へ拡張しない。

まず一致/不一致を予想し、条件ボタンをクリックして確定→保存表示→途中境界と全suffix比較→原典/実装→答えの順にする。保存記録の欠落/改変を表示が拒否した場合、古い答えを使わず正常記録へ戻す。実行未済やGUI未確認を確認済みへ読み替えない。
