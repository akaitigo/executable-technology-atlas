---
name: stream-half-close
description: streamの受信EOFと逆方向送信の関係を、専用socketpair原票とhalf-close教材で学ぶ。
---

# 方向を分けてEOFを読む

2階層上のCONTRACT.mdの手表を先に読む。README.mdのコマンドで保存原票のUIを開く。AのSHUT_WR、Bの0-byte recv、Bの返信sendall、Aの返信とEOFをstepで追う。Bのrx=eofでもtx=openが残る正常例と、返信省略の故障対照を比較する。

header/body途中EOFと正常拒否ERR、timeout、execution_failureを同じ成功に数えない。recv chunkをpacket/frameと呼ばず、独立oracleへ合計bytesで照合する。Unix domain streamからTCP FIN/WAN/TLSの実測を主張しない。保存原票の読み取りと--freshの新しい専用socketpair実行を区別する。

検証はverify.pyとroute.py。通常学習で--record/--seal-recordを実行して原票を変更しない。元教材やglobal indexを編集しない。他者のsocket/server/tabを操作しない。
