# accept後の別base chain drop

元[Network Platform Security](../../../subjects/network-platform-security/README.md)が未教材として挙げた、accept後の別chain dropだけを扱う独立教材です。Python標準ライブラリで合成JSON packetを実計算します。nftablesの構文パーサーや実kernel試験ではありません。

同じinput hookのbase chainをpriority 0→10で評価します。source chainは10.0.0.1をaccept、それ以外をpolicy drop。service chainはtcpかつdst port 22をdrop、それ以外をpolicy accept。正常版はacceptの後に次chainへ進み、dropで全体を終えます。故障版は最初のacceptをruleset全体の終了へ取り違えます。

|入力|正常|故障|決め手|
|---|---|---|---|
|trusted tcp/22|drop|accept|priority 0 accept後、10でdrop|
|trusted tcp/8080 またはudp/22|accept|accept|最終verdictは同じでもtraceは違う|
|unknown source|drop|drop|priority 0のpolicy drop、service未訪問|
|trusted tcp/22、service disabled|accept|accept|後chainなしの対照|
|chain JSON逆順|上記と同じ|上記と同じ|入力配列順ではなくpriorityでsort|

## 契約と一次資料

[Netfilter公式manpage](https://netfilter.org/projects/nftables/manpage.html)のOVERALL EVALUATION OF THE RULESETとVERDICT STATEMENTSを2026-10-06 JSTに確認しました。低priorityからbase chainを評価し、acceptは現在のbase chainの評価を終え、次のbase chainへ進みます。dropはruleset評価を終え、後chainで覆せません。同priorityの順序は実仕様では未定義です。

この教材は同priorityを`duplicate_priority`として独自に拒否します。JSONはpacket/chainsだけ、chainはsource/service各1個、hook input、priority固定0/10、固定accept/drop ruleとpolicyです。sourceは常時enabled、serviceだけ無効化できます。packetはcanonical IPv4文字列、tcp/udp、exact int port 0..65535。boolをintへ変換しません。未知verdict、非有限JSON数値、重複key、壊れたJSON、型・範囲・固定subset外をpacket評価前に拒否します。これは実nftablesの全verdictを無効とする主張ではありません。

[expected-table.json](expected-table.json)はproducer作成前に固定した18ケースのfull trace/final oracleです。evaluatorをimportして期待値を作りません。[contracts](contracts.json)、[source](evaluator.py)、[sources](sources.json)、[coverage](coverage.json)を併読してください。

## 実行とUI

```sh
python3 -B checker.py
python3 -B runner.py
python3 -B runner.py --record
python3 -B server.py --record
python3 -B qa/check-ui.py
```

最初の2つとQA checkerは全unitファイルのSHA256/mtimeを維持するread-only検証です。明示`--record`だけ新しいUTC IDの原票を書きます。旧原票は追記・上書きしません。runnerはobservation-data.jsを現在原票の索引として更新します。serverは所有loopback動的portのunit内previewのみ。system nft/firewall/packet送信コマンドはありません。停止はその所有serverだけです。生成物の相対pathで原票とsource hashを結びます。

UIは予想→操作→正常/故障→一次資料/source/raw→実入力の答えです。textareaの各入力をPython subprocessへ送って実計算し、返ったpacket/final/fulltraceから本文を作ります。固定表への文字列置換ではありません。例・予想・JSON変更と比較開始では本文/trace/verdict/requestを空にし、detailsを閉じ、新入力を保持します。subset拒否・通信/実行失敗に正常答えを出しません。revisionの古い応答は破棄します。previewの600ms応答遅延はこの競合を検証するためだけです。

実IAB、変更時reset、編集入力、subset拒否、古い応答、server停止時失敗、capture、リンクとcleanupの実原票は[QA](qa/README.md)に記録します。MarkdownをIABがblockedにした場合は、その制限を記録して回避しません。元Subjectリンクはunit-only serverから配信せず、filesystemで検証します。

## 未検証

conntrack、NAT、fragment、他hook、regular chain jump/goto/return、実kernel差、実packet配送、firewall安全性、実設定への変換を検証していません。synthetic acceptは実通信成功を保証しません。旧Subject、Portal、他unitを変更せず、この有限unitをfreezeします。
