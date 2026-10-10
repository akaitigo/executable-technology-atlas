# UDP: 空のmessageと消える末尾

第1単元[TCP streamとframing](../../../subjects/networking-protocols/README.md)を読み、[LEARNING_PATH実験2](../../../subjects/networking-protocols/LEARNING_PATH.md)へ進む追加単元です。原入口97件を変更・再実装せず、UDPの受信単位と終了の意味を深掘りします。

## 前提 → 問い

byte列、IPv4の端点（address/port）、bufferの最大幅、返り値と例外を知っていることが前提です。TCPではrecvのchunkを蓄積してframeを切り出しました。UDPで同じ受信処理を使うと、空payloadや受信幅不足をどう扱ってしまうでしょうか。

| 条件 | literal送信payload | recvfrom幅 | 実行前の手書き期待（Mac / flags0） |
|---|---|---|---|
| two-datagrams | PING / HELLO | 64 / 64 / 64 | PING / HELLO / timeout |
| empty-datagram | b'' / NEXT | 64 / 64 / 64 | b'' + sender / NEXT / timeout |
| small-buffer | ABCDEFGHIJ / NEXT | 3 / 64 / 64 | ABC / NEXT / timeout |
| exact-fit | ABC / NEXT | 3 / 64 / 64 | ABC / NEXT / timeout |

[contracts.json](contracts.json)にsentのliteral hex・幅・受信期待を先に固定し、checkerにも独立literal契約を手書きしました。実行実装へはexpectedを渡しません。実行が期待と違えばcheckerは失敗し、原票を残します。到達や順序は今回の小さいloopback条件についての予想で、UDP全体の保証ではありません。

## 予想 → 操作 → 比較 → 原典 / 実装 → 答え

[UI](index.html)は保存した実API原票を1 recvずつ再生します。ブラウザでUDPを再実行しません。

1. 条件を選び、空をEOF扱いするか、末尾を次recvで拾えるかを予想する。
2. 「recvを1回進める」でpayload bytes・sender・呼出し幅を読む。最後はtimeout例外を読む。
3. datagramごとの候補、TCP EOF扱い版、stream連結版を比較する。候補を業務messageとして検証済みとは扱わない。
4. send原票、手書き期待、[独立checker](checker.py)、[実API実装](observe_udp.py)、[故障prototype](policies.py)、[原典locator](sources.json)へ戻る。
5. 答えを開き、十分な幅で返ったdatagram、空payload、切捨て、timeoutを分ける。

```sh
# 通常検算: socketを開かず、ファイル更新もしない
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
# 明示採取だけが4条件の所有UDP socketを開き、新しいrunを保存する
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record
# UI preview（表示portは端末の実出力を読む）
python3 -u -m http.server 0 --bind 127.0.0.1
```

server終了はCtrl-C。runner引数なしはexit1で更新を拒否します。新runはobservations配下、commandの実stdout/stderr/exit、UTC時刻、環境、source/input/artifact SHA256を記録。前run・失敗を消さず、exit0時だけobservation-data.jsを更新します。既存rawのcheckerはそのrawが採取されたsourceに束縛されるため、実装変更後は明示再採取が必要です。

## 観測経路と有限性

標準Python / AF_INET / SOCK_DGRAM / recvfrom(flags=0)。127.0.0.1だけを使い、各caseはsender/receiverを別の動的portへbind。2回sendtoしてから同threadで3回recvfrom。socket timeout0.3秒、外側child timeout8秒、各caseに再送・retryなし。threadを作らず、finallyで各2socketをcloseしfilenoとowned countを記録します。timeout8秒はOS障害時の上限で、0.3秒はこの有限ローカル測定の待ち時間、実ネットワークの再送基準ではありません。

少数loopbackの到達・同順序・timeoutは実測しても、UDP配送・順序・重複排除・相手の停止を保証しません。第3timeoutは送信した8datagramの後に追加dataを観測しなかった結果で、loss発生やpeer EOFを示しません。API原票でありpacket captureではなく、wireのUDP/IP headerやMTUは測っていません。

[QAと実測結果](qa/README.md)にrun、検算、実IAB、保存画像、制限・owned cleanupを記録します。全Subject/Atlas完成・Core gate・formal deliveryを主張しません。

## 誤解を実務判断へつなぐ

- **空はmessageとして渡す。** この実験ではsendto(b'')が0を返しても空datagramが届き、senderも返る。TCP EOF扱い版は直ちに停止してNEXTを見落とす。空を許可するか拒否するかはアプリ契約で決め、transport EOFにしない。空payloadにもUDP/IP headerがある。
- **不足幅の末尾はstream bufferへ残らない。** 今回の10-byte入力はABCを返し、次はNEXT。連結版はABCNEXTを作り、別messageを混ぜてもDEFGHIJは戻らない。小さいrecvfromの結果を完全な業務payloadとして処理しない。
- **len==bufsizeは判定材料として不足。** 幅3の両条件は同じABC。今回はsent原票を持つので切捨てが分かる。汎用受信側では、この方法だけで切捨てを検出できない。アプリ最大長を決め、最大長+1の受信幅でoversizeを拒否するか、OS対応のrecvmsg/MSG_TRUNCとpayload内の長さ検証を検討する。今回はどちらも未実装。
- **sender addressは認証ではない。** checkerは所有sender端点との一致を検算するが、spoofing耐性や相手の信頼性を検証していない。
- **send成功は業務ackではない。** sendtoの返却bytesは相手の受信・検証・永続化・処理完了の証拠にならない。この実験には業務ackはない。必要ならrequest ID、ackが示す段階、重複処理、timeout後の副作用をprotocolで定める。

境界を保った低遅延messageが目的でも、UDPが自動で信頼性を提供するわけではありません。欠落しても次の更新でよいtelemetryと、必ず一度だけ副作用を起こす操作を同じ設計にしない。自前再送・順序制御・輻輳制御が必要ならRFC8085を読み、既存transportを選ぶ判断も行います。

## 原典と観測の関係

[Python3.9 socket](https://docs.python.org/3.9/library/socket.html)のrecvfrom/sendto/settimeoutは返り値と例外を読む入口。資料は3.9.25で、runtimeはraw環境欄の実版です。[Apple archived recvfrom(2)](https://developer.apple.com/library/archive/documentation/System/Conceptual/ManPages_iPhoneOS/man2/recvfrom.2.html)のDESCRIPTION/MSG_TRUNC/RETURN VALUESは切捨てとTCP return0の意味を読む資料で、2006年manualを現Darwinの実測へ置き換えません。[RFC768](https://www.rfc-editor.org/rfc/rfc768.html) Introduction/User Interface/Lengthと[ RFC8085](https://www.rfc-editor.org/rfc/rfc8085.html) §3.2/3.3は、message単位と信頼性/サイズの判断へ接続します。取得不能のOpen Group URLもsources.jsonに残しています。

## 今回のcoverage増分と残る次実験（未実行）

増分はUDP recvfromのdatagram境界、空payloadとTCP EOFとの差、幅不足の切捨てとexact-fit対照、timeoutとsend成功の意味です。TCP framing/EOF境界の再実装、入口数の加算は行いません。

| 次の具体実験 | 問い・入力・独立予想 | 原典locator |
|---|---|---|
| 1. 受信完全性の契約 | 最大payload8に対し0/8/9/16 bytesを送る。幅9でoversize拒否と、recvmsg MSG_TRUNCの実flagを別API条件で比較。切捨てを小payloadと誤認しないことを独立fixtureへ照合する。 | Python recvmsg / Apple MSG_TRUNC / RFC8085 §3.2 |
| 2. 業務ackと重複 | socketを使わない有限traceでrequest ID、処理後ack喪失、同ID再入力を与える。副作用1回とackの意味を手書きstate traceへ照合。実配送保証とは主張しない。 | RFC8085 §3.3 Reliability / §3.1 Congestion Control |
| 3. backpressureと上限 | 元LEARNING_PATH実験3。producer/consumer仮想時計と有限byte列でqueue上限・停止/再開を照合。kernel buffer/TCP windowの実測とは分ける。 | 元LEARNING_PATH / RFC9293 §3.8 / Socket HOWTO Non-blocking |

routing/DNS/IPv6/MTU/NAT/TLS/HTTP/実WAN loss・再送・輻輳・本番認証は残る未教材。次実験は自動開始しません。
