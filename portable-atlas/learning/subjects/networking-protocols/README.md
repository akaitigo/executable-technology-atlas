# TCP streamとアプリのframing

問い: `sendall`を2回呼んだら、`recv`も2回で1件ずつ返るのか。

Mac loopbackの標準Python socketで合成入力 `PING` / `HELLO` を実送受信した。6 + 7 bytesの2回のsendallに対し、今回のrecv(3)は3 + 3 + 3 + 3 + 1 bytes、recv(64)は13 bytesを1回で返した。長さを見て蓄積するparserは両条件で2件を復元し、1 recv = 1 frameのparserは両条件で復元できなかった。異常はアプリの境界仮定であり、TCPの通信failureではない。

## 画面を開く

このdirectoryで標準PythonのHTTP serverを起動する。

```sh
python3 -m http.server 4189 --bind 127.0.0.1
```

`http://127.0.0.1:4189/` を開き、予想を選ぶ → recvを1回ずつ進める → 2つのparserを比較 → 公式一次資料・実装へ戻る → EOFで答えを確認する。読み出し幅を切り替えると、同じ13 bytesの別の実観測を再生できる。終了はCtrl-C。

画面操作は保存済み実観測の再生で、ブラウザがTCP実験を再実行するものではない。byte図とSequence図はAPI原票を読みやすくした説明図で、packet captureではない。

## 実観測の再現

外部依存・Docker・packet capture不要。127.0.0.1の動的portで2接続だけ実行し、各socket timeout 3秒、各接続recv 32回、外側command timeout 20秒を上限とする。正式な実行許可が必要な環境では、socket listenを含む以下のcommandへ許可を適用する。拒否時は別手段で迂回しない。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 record_observation.py
```

入力は2-byte big-endian長さ＋本文のアプリ独自形式。sendall #1は `00 04 50 49 4e 47`、#2は `00 05 48 45 4c 4c 4f`。受信開始前に2回のsendallとSHUT_WRの完了をアプリ内Eventで待つ。この待ち合わせとrecvの最大幅によって、境界依存parserの問題をboundedに観測する。TCP segmentの分割やdelayを設定していない。

runごとに `observations/<execution-id>/command.json` がcommand・exit・生stdout/stderrを保持し、成功時に `observation.json` / `manifest.json` を追加する。前runを上書きしない。成功した観測だけ `observation-data.js` をatomic replaceして画面へ接続する。失敗時はcommand記録を保持し、画面の直前成功データを変えない。

## 今回の原票

- 実行ID: `20261005T042706961417Z-tcp-stream`
- UTC: `2026-10-05T04:27:07.032037Z` — `2026-10-05T04:27:07.033752Z`（日本時間13:27）
- CPython 3.9.6 / Darwin 25.1.0 / arm64 / AF_INET・SOCK_STREAM・TCP
- 内部command: `python3 observe_tcp.py`、exit 0、stderr空、attempt 1 / retry 0
- 2条件ともlistener/client/accepted socket各3個をclose、open_owned_sockets 0、sender thread終了
- [実API原票](observations/20261005T042706961417Z-tcp-stream/observation.json) / [command生出力](observations/20261005T042706961417Z-tcp-stream/command.json) / [Artifact digest](observations/20261005T042706961417Z-tcp-stream/manifest.json)

Python docsは同系列の3.9.25を参照し、実行runtime 3.9.6とは区別する。[RFC 9293 §2.2](https://www.rfc-editor.org/rfc/rfc9293.html#section-2.2)はTCPのbyte streamサービスを、[Python socket API](https://docs.python.org/3.9/library/socket.html#socket.socket.recv)はrecv/sendallを、[Socket HOWTO](https://docs.python.org/3.9/howto/sockets.html#using-a-socket)はアプリ側のframingを説明する。第三者本文は保存していない。[sources.json](sources.json)に版・locator・Coverageを保持する。

## 検算

```sh
PYTHONDONTWRITEBYTECODE=1 python3 test_lesson.py
node --check app.js
```

checkerはsocketを開かず、13 bytesの全4096分割でlength decoderが2件を復元すること、不完全EOF・不正長さ・分割/連結を1 frameと決める失敗、実原票のbytesとparser結果・Source/Artifact digest・cleanupを検査する。この分割網羅はparserの合成入力試験であり、4096条件のTCP実測ではない。

## Scopeと未教材Coverage

Catalog IDは `networking-protocols`。この1教材の対象はTCP stream API境界とアプリのlength framing。DNS、UDP、L2、IP routing、handshake packet、loss、再送、輻輳制御、TLS、HTTP、負荷分散、IPv6、WAN、production backpressureは未教材・未実測。recv(64)が13 bytesを返すことやrecv(3)が常に3 bytesを返すことは保証しない。送信成功と相手の業務処理完了は別である。

今回の教材受入は分野全体、学習者の理解度、既存Atlas Completionを完成扱いするものではない。専用directory以外、Portal catalog、root README/docs、元Subject、Core/Graphへ書き込まない。ローカル教材で公開・commit・pushなし。

再利用入口は [skills/atlas-networking-protocols/SKILL.md](skills/atlas-networking-protocols/SKILL.md)。このSkillは教材内だけに置き、global installや他Subjectへの適用を行わない。

今回の操作受入、デスクトップ/モバイル実画面、Skillの限定依頼例、cleanup確認は [qa/QA.md](qa/QA.md) に記録した。
