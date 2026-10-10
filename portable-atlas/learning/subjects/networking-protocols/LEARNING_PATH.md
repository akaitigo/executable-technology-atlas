# ネットワークとprotocolを学ぶ道筋

この文書は[TCP streamとframingの既存教材](README.md)から、通信単位、終了・異常境界、資源制限へ進むための補足です。有限教材の補足であり、分野全体の学習完了を示すものではありません。以下の次実験はすべて未実行です。

## 1. 前提と仕組み

byteと文字の違い、整数のbig-endian表現、buffer、関数の返り値と例外を理解します。TCP/UDPのsocketを読む前に、接続の端点を示すIP addressとport、アプリが解釈するmessageを分けます。

学ぶ順序は **端点と層 → byte stream / datagram → アプリのframing → EOF・timeout → bufferとbackpressure → routing・loss・再送 → TLS・HTTP等の上位protocol** です。

- TCPの送受信API呼出し、TCP segment、アプリmessageは別の単位です。`recv`のchunkをpacketとして数えません。
- streamからmessageを取り出すには、固定長、delimiter、長さprefixなどの契約が必要です。本文の長さは文字数かbyte数かも決めます。
- `recv(n)`のnは最大幅です。必要なbyteが揃うまで蓄積し、一度のchunkに複数frameがあれば繰り返し取り出します。
- EOFは受信方向の終了です。message途中でのEOF、timeout、正常にframeを読み終えたEOFを同一視しません。
- `sendall`成功は相手の業務処理完了ではありません。アプリのackや再実行の契約は別に定めます。

## 2. 予想から既存実測へ

[UI](index.html)で「2回sendなら2回recvか」を予想し、[TCP観測実装](observe_tcp.py)、[parser](framing.py)、[実API原票](observations/20261005T042706961417Z-tcp-stream/observation.json)、[commandと生出力](observations/20261005T042706961417Z-tcp-stream/command.json)を読みます。この文書作成ではsocketを開かず、再実行していません。

| 観測条件 | 保存済みdata recv | 正常parser | 境界依存の異常parser |
|---|---|---|---|
| recv最大幅3 | 3 + 3 + 3 + 3 + 1 bytes | PING / HELLOの2件 | frameを復元できない |
| recv最大幅64 | 13 bytesを1回 | 同じ2件 | 連結frameを1件とみなし拒否 |

入力は2-byte長さprefixと本文で、sendallは6 / 7 bytesの2回です。受信開始前に2回の送信とSHUT_WR完了を待つ条件が置かれています。このMac loopbackの実測は、recv境界とframe境界が一致しない反例です。TCP通信のfailureを示すものではなく、同じchunk分割が次回も再現する保証もありません。

recv最大幅3ではdataが5回、EOFを返す0-byte recvまで数えると6回です。[QA](qa/QA.md)の4096分割検査は13-byte入力のparser試験であり、4096回のTCP実測ではありません。図はAPI原票の説明で、packet capture、再送、輻輳、WAN遅延の証拠ではありません。既存のparserは長さ1〜1024を受け入れ、不正長さと不完全EOFを拒否する契約です。

## 3. 実務で何を判断するか

受信処理ではchunkごとに業務処理を開始せず、完全なframeを切り出してから検証します。長さ上限、接続全体のbuffer上限、待ち時間、異常後に接続を継続するかを別々に定めます。frame上限だけでは、待機接続数や未処理messageの蓄積を制限できません。

protocolを選ぶときは、順序と配送、重複、遅延、接続状態、認証と暗号化を要求ごとに比較します。loopbackで成功しても、DNS、routing、MTU、再送、TLS検証、proxyの条件は未評価です。相手に処理を依頼するなら、request ID、ackの意味、timeout後の再送による副作用も設計します。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [RFC 9293](https://www.rfc-editor.org/rfc/rfc9293.html)、§2.2 Key TCP Concepts、§3.6 Closing、§3.8 Data Communication | streamの契約から終了・再送・windowへ進む |
| [Python socket API 3.9](https://docs.python.org/3.9/library/socket.html)、recv / send / sendall / recvfrom / settimeout | APIの返り値、最大幅、timeoutの境界 |
| [Python Socket HOWTO 3.9](https://docs.python.org/3.9/howto/sockets.html)、Using a Socket / Disconnecting / Non-blocking Sockets | framing、部分送受信、終了、readinessの読解 |
| [RFC 768](https://www.rfc-editor.org/rfc/rfc768.html)、冒頭のservice説明 / User Interface | UDPのdatagramと配送・重複保護の保証範囲 |

既存bindingは[sources.json](sources.json)にあります。Python資料は3.9.25、既存観測runtimeは3.9.6であり、同じ実行版の証拠ではありません。

## 5. 未教材の問いと次実験

| 未教材 | 問い | 次の入口 |
|---|---|---|
| framingの広い異常入力 | header途中・本文途中・byte長の境界で何を拒否するか | 実験1 |
| UDPとprotocol選択 | datagramとstreamで受信・終了の意味はどう違うか | 実験2 |
| backpressureと資源制限 | 消費が遅いとbufferはどこまで増えるか | 実験3 |
| L2、IP routing、IPv6、DNS、MTU | 端点へ到達する経路や名前解決はどう決まるか | 別教材。今回のloopback原票では答えられない |
| handshake、loss、再送、輻輳、WAN | segmentと時間・負荷の挙動をどう観測するか | RFC 9293の該当節から別の測定計画へ |
| TLS、HTTP、負荷分散、業務ack | 相手の信頼とmessage・処理完了をどう定めるか | 上位protocolの原典と別教材が必要 |

## 6. 次の実験案（3本、すべて未実行）

1. **EOFと長さ境界をparserだけで比較する。** 独立fixtureとして長さprefixの1-byte切断、本文の途中切断、長さ0 / 1 / 1024 / 1025、UTF-8の複数byte文字、2件連結を用意します。予想は完全な許可長だけを復元し、不正長さと途中EOFを拒否することです。期待本文をbyte列で先に固定し、各feed後のemitted/bufferとfinish結果を照合します。socketを使わない合成検査と明記し、文字数をprefixにした故障版も比較します。原典はSocket HOWTOのUsing a Socketです。

2. **UDPのmessage単位をTCP原票と比較する。** 実施時には専用loopback・動的port・2合成datagram・十分な受信buffer・有限timeoutを固定し、recvfromのpayloadと送信元を記録します。予想はTCPの13-byte streamと異なり、datagram単位を読めることです。小さい受信bufferの条件は別runにし、返却byteとOS/API上の切捨ての扱いを記録してから解釈します。未到達・timeoutも結果として残し、少数loopbackの到達から配送保証・順序・重複排除を推論しません。UDPの空datagramをTCPのEOFと混同しない比較も加えます。原典はRFC 768とPython recvfromです。

3. **遅い消費者とbuffer上限を仮想時計で比較する。** 実socketの代わりに有限producer/consumer modelを作り、1tickで投入するbyte数と消費数を固定します。無制限queueと、上限到達時にproducerを止める方式を比較し、queue長・停止・再開・最終byte列を手書きtraceへ照合します。予想は無制限版で滞留が増え、制限版では上限を守る代わりにproducerが待つことです。frame順序と欠落も検査します。RFC 9293 §3.8のwindowとHOWTOのnon-blockingを読む入口ですが、独自queue modelはTCP window・kernel buffer・production throughputの実測ではありません。

## 7. 資料の取得・検証状況

2026-10-05に上記4資料のHTML本文を取得して参照箇所を確認しました。今回取得不能だったURLはありません。第三者本文・図・コードは保存していません。

追加したのはこの文書だけです。socket、server、parser test、UI、global gateは実行せず、既存原票・QA・digestを更新していません。次実験の予想は新たな実測証拠ではありません。
