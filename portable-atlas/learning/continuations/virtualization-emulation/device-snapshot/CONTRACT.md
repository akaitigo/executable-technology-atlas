# Atlas：小装置のsnapshotと継続実行の契約

## 問いと範囲

同じ命令位置、レジスター、メモリーを復元しても、タイマーの途中位置や保留状態が欠けると、その後の読み値は同じでしょうか。目標16と元COVERAGEの次3に対し、固定の小装置を含む完全状態の保存・復元を追加します。Tiny8の幅、STORE、コードキャッシュ失効は前提で、再実装・再加算しません。

作者定義の固定10命令とメモリー4byteだけです。命令のバイナリー符号化、ジャンプ、割込みの自動配送はありません。仮想tickだけを進め、host clock、sleep、実I/O、QEMU、HVF、実VM、分離、物理時間、live migrationを実行しません。

## 完全状態と固定構成

状態は厳密に `pc, a, memory, tick, device` の5欄です。pcは次の命令のindex、aとmemory各要素は0..255の整数、memoryは4要素です。tickは完了した命令数で、今回pcと同じ0..10です。deviceは `counter`（0..2の整数）と `pending`（bool）だけです。boolを整数欄へ許可せず、floatも拒否します。

初期状態は pc=0, a=7, memory=[0,0,0,0], tick=0, counter=0, pending=false。機種名は `polling-timer-v1`、周期は3。構成と命令列はfixturesに固定し、任意のISA/機種の入力は受け付けません。

|pc|命令|タイマー更新後の命令効果|
|---|---|---|
|0,1,2|NOP|aとmemoryとpendingを変更しない|
|3|READ|a = pendingなら1、そうでなければ0。読み取りではpendingを消さない|
|4|STORE 0|memory[0] = a|
|5|ACK|pending=false。counterは変更しない|
|6|READ|同上|
|7|STORE 1|memory[1] = a|
|8|READ|同上|
|9|STORE 2|memory[2] = a|

## 1命令の順序と観測

1. pc<10の境界からtickを1増やす。
2. counterを1増やす。3になればcounter=0、pending=trueへ設定する。既存pending=trueでも発火を記録するが、回数をpendingへ蓄積しない。
3. 当該pcの命令を実行する。READ/ACKはこのタイマー更新後のpendingを読む/消す。
4. pcを1増やして境界状態を保存する。pc=10は終了で、追加tickは進めない。

tick6では発火→ACKの順なので、その境界のpendingはfalseです。これは作者が定めた優先順で、実ハードウェアの割込み優先度の再現ではありません。READの観測値は各命令の後に追加する別の出力記録で、装置に戻さない。snapshotは4の境界だけで取り、命令の途中は対象外です。

## 4条件と3経路

|ID|prefix完了数cut|切断点のdevice|比較する問い|
|---|---:|---|---|
|initial|0|0,false|まだ装置履歴がない場合、故障版も同じになるか|
|before-expiry|2|2,false|発火直前のcounterが落ちると、READはいつ変わるか|
|pending-latched|3|0,true|発火済みpendingだけが落ちると、READはどう変わるか|
|after-ack|6|0,false|ACK後に両欄が既定値なら、同じ故障が今回観測されないか|

各条件で初期状態からcutまで同じprefixを実行し、次の3経路を比較します。

- continuation：切断点の完全状態からそのまま継続。
- full-restore：完全snapshotをJSON文字列へ保存し、JSONとして読み戻し、厳密検証して継続。
- omit-device：比較専用の別schemaでdeviceだけを省略し、counter=0/pending=falseを補って継続。pc/a/memory/tickは保持するので、時計リセットの影響を混ぜない。

suffixはcut境界を最初に含み、最後のpc=10までの全状態、全timer発火、READ観測、STORE/ACKを保存します。完全復元はcontinuationとsuffix全値が一致することを期待します。故障版は初期/ACK後で一致しても、一般の復元正しさの証拠にはしません。snapshot保存は元状態を変更しません。前のREADログをsnapshotへ含めず、比較するのは復元後のsuffixのREAD列です。

## 保存形式と拒否

完全snapshotは `{"schema":"atlas-device-snapshot","version":1,"machine":"polling-timer-v1","state":{...}}`。全key集合、整数/bool型、各範囲、memory長、pc=tickを厳密に検証してから1命令目へ進みます。versionのbool/float、未知version、missing/extra key、未知schema/機種、不正状態を拒否し、更新0/READ0とします。独自の互換処理や既定値の黙った補充はしません。pickle、ファイルパス入力、ネットワークは使用しません。

故障版のschemaは `atlas-device-snapshot-omit-device-demo`。stateはdevice以外の4欄で、専用の比較関数だけが既定deviceを補います。完全restoreにこのschemaやdevice欠落を渡す場合は拒否であり、故障版が正常restoreの許可経路になることはありません。

fixturesは完全固定の型付き値に照合してから全条件へ入り、不正fixturesなら全経路更新0です。snapshot単体の拒否はその復元経路更新0です。実装前の手表と独立表を別保存し、snapshotのhashはbytes対応だけで、改ざん防止・認証・互換性の証明とは扱いません。

## 原典と未検証

QEMU公式Migration frameworkの「Saving the state of one device / General advice」は装置内部の状態も保存対象になることを説明します。「VMState / Versions」は欄と形式の版を扱います。本教材のdict、周期3、命令順、既定値故障はその実装ではなく独自規約です。

継続一致はこの4条件・固定suffixだけの有限確認です。任意のプログラム、実ISA/VM互換、全装置、並行実行、割込み配送、セキュリティ隔離、live migration、性能、実時間の決定性は保証しません。対象計算と実画面は別の実行記録が保存されるまで未実施です。
