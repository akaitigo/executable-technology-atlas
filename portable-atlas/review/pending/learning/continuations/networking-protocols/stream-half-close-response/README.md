# streamのhalf-close後に返信を受け取る

Aは要求を送ってSHUT_WRし、Bは要求とEOFを受け取ってから返信します。Bの受信EOF時にも送信側はopenです。正常版はACKまたはERRを返し、Aは返信とEOFを受信します。故障対照はBが両方向完了と誤解して返信を省き、AはreplyなしEOFを受け取ります。

## 学び方

このディレクトリで以下を実行します。標準ライブラリだけを使います。

```sh
python3 -B verify.py
python3 -B verify.py --fresh
python3 -B route.py
python3 -B serve.py
```

verifyは保存原票と独立oracle・合成検査を照合します。--freshは新しい専用socketpairで36件と2失敗probeを再観測します。原票を上書きしません。serveが表示する自分のlocalhost URLを開き、fixture/方式/recv幅を選び、EOF後の返信を予測します。画面は保存済の実API原票を読み、socketを再実行しません。stepでA→B、B→Aを分けて追い、各端点のtxとrxを確認します。終了は自分のサーバだけにCtrl-C。

完全frame、header途中、body途中のEOFを別に読みます。拒否ERRも返信です。timeoutはEOFでもprotocol拒否でもありません。実行失敗も正常な拒否に数えません。recvの返却chunkはpacketやframeとして数えず、合計bytesを手表と照合します。幅1/64でも同じ合計・意味になった事実から、次回のchunk境界が同じだとは推論しません。

## 証拠と限界

CONTRACTの手表を実装前に固定しました。observations/attempt-01/raw.jsonにMacの実socketpair36件、実timeoutと閉じたsocketのrecv失敗各1件、環境・初回source hash、81合成分割、16入力拒否、6mutant検出を保存しています。observe.pyは単一の呼出threadで順次小さい送信を行い、各socketのtimeoutとrecv回数/bytes上限を設け、finallyで両socketをcloseします。専用childthreadは使いません。close後fileno=-1を記録しています。

UIの状態図は成功APIに基づく論理状態で、kernel内部状態やpacket captureではありません。Unix domain streamの実測であり、TCP FIN、外部到達性、WAN、TLSを観測していません。元TCP/UDP教材とLEARNING_PATHは変更していません。既存§6実験1の全長さ・全parser境界の完成とは扱いません。全Core audit/repository gateは本単位では未実行です。

## 一次資料と版

- [Python socket API socketpair](https://docs.python.org/3/library/socket.html#socket.socketpair)は接続済pairの生成を説明します。
- [shutdown](https://docs.python.org/3/library/socket.html#socket.socket.shutdown)はSHUT_WRによる送信方向終了を説明します。
- [Socket HOWTO Disconnecting](https://docs.python.org/3/howto/sockets.html#disconnecting)は要求送信→shutdown(1)→serverの0-byte recv→返信の関係を説明します。本教材は不完全frameのEOFを成功requestと同一視しません。

取得した現行文書は3.14.8、既存資料の[API3.9](https://docs.python.org/3.9/library/socket.html)と[HOWTO3.9](https://docs.python.org/3.9/howto/sockets.html)は3.9.25、実runtimeは原票の3.9.6です。文書版と実行版を区別します。第三者本文は保存していません。
