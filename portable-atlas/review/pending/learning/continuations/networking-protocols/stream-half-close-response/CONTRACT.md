# EOFは受信方向の終了

専用所有のMac stdlib `socket.socketpair(AF_UNIX, SOCK_STREAM)`で、A→B要求、B→A返信を観測する。外部network、bind、設定変更、worker threadは不要。各socket timeoutは2秒、全処理は有限send/recv回数。全byte上限128、recv上限130回、両socketをfinallyでcloseしfileno=-1を記録する。close前にSHUT_WRで送信方向だけを終了する。

Aが固定bytesをsendallしSHUT_WRする。Bはrecvを0-byte EOFまで繰り返す。normalはframeの分類に応じ返信frameをsendallしSHUT_WRする。Aは返信とEOFを読む。faultはBが受信EOFを両方向完了と誤解し、返信を省略して自分の送信側をSHUT_WRする。Aは返信なしEOFを観測する。faultは実API故障ではなく意図的なprotocol応答欠落。

frameは2-byte unsigned big-endian本文長と本文。要求は1〜16bytesの1frameのみ。返信本文はACK:と要求本文、または下記ERR文字列で、同じ2-byte prefixを使う。UTF-8はbytesとして返し、要求の文字decodeを要求しない。Bの正常な拒否も返信を送る。完全headerなしはheader_eof、有効長さの本文不足はbody_eof、長さ0/17以上はinvalid_length、本文後の余分bytesはtrailing。検証優先順はheader→長さ→本文→trailing。空streamもheader_eof。

## 実装前に固定する手表

| fixture | A要求hex | B判定 | normal返信本文 | fault返信 |
|---|---|---|---|---|
| ping | 000450494e47 | complete | ACK:PING | なし |
| utf8 | 0002cf80 | complete | ACK:π（UTF-8 bytes） | なし |
| maximum | 00104142434445464748494a4b4c4d4e4f50 | complete | ACK:ABCDEFGHIJKLMNOP | なし |
| header | 00 | header_eof | ERR:header_eof | なし |
| body | 00045049 | body_eof | ERR:body_eof | なし |
| empty | 空 | header_eof | ERR:header_eof | なし |
| zero | 0000 | invalid_length | ERR:invalid_length | なし |
| over | 0011 | invalid_length | ERR:invalid_length | なし |
| trailing | 0001505a | trailing | ERR:trailing | なし |

recv最大幅1/64を別runで観測する。各runの返却chunksを合計bytesで独立oracleと照合し、chunk境界不変、packet、frame数を推論しない。UIは保存観測を読むだけでsocketを再実行しない。normal/refusalはprotocol判定、timeout/execution_failureは実行状態として別fieldで表示する。意図的timeoutは未送信・未shutdownのpairのB.recvを0.02秒で待つ1回、意図的execution_failureは閉じたB.recvの1回。どちらもfinally closeする。

API traceは成功・EOF・例外の返却と、A/Bのtx（open/shut_wr/closed）、rx（open/eof/closed）状態を含む。EOFを観測したBのtxがopenのまま返信sendall成功することを正常例で確認する。sendall成功だけで業務処理完了を主張しない。

Unix domain streamの実測であり、TCP FIN、packet、外部到達性、WAN、TLSの実測ではない。既存§6実験1の全長さ・全parser境界の完了を主張せず、元教材・LEARNING_PATHを変更しない。
