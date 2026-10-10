# Kotlin：smart castが成立する境界

**制作状態：固定Kotlin 2.4.10 / OpenJDK 17.0.17でcompile 3条件・runtime 6条件を実行し、独立検証49項目が通過しました。** 2026年10月6日14:46 JSTの[実測・答え合わせ](observations/operational-revision-20261006T054006019240Z/README.md)を保存しています。正常終了5条件、意図したruntime NPE 1条件、compile拒否2条件を分離しています。保存原票readerの作者GUI QAは24項目・91実ポインター操作で通過し、1280/390幅の実capture 7枚を目視しました。別reviewerによる独立受入とAtlas統合は別の状態として管理します。



前教材[「同じString?のnull演算子比較」](../kotlin-null-operators/README.md)では、安定した関数引数をnull検査しました。次は、propertyを2回読むと同じ値とは限らないことを考えます。[操作画面](index.html)は、変更していない原票を取得しSHA-256を照合して表示するreaderです。画面内の流れは模式図であり、実行traceやcaptureではありません。

画面は教材のルートで次を起動し、表示された127.0.0.1のURLをブラウザで開いて使います。port 0は空きportをOSに選ばせます。終わったらCtrl+Cでこのserverを終了してください。HTMLをファイルとして直接開いた場合は取得できない旨とHTTPで開く手順を表示します。

~~~sh
python3 -m http.server 0 --bind 127.0.0.1
~~~

条件と予想を選ぶ→保存原票を読む→正常/異常を比較する→原典・実装を読む→予想と照合する、の順で進めます。画面のボタンはKotlinやJVMを起動しません。

## 到達目標

1. 変更可能なpropertyのnull検査が、後の読取りを保証しない理由を説明する。
2. 独自getterを持つval propertyと、ローカルvalを区別する。
3. 一度読んだ値をローカルvalに受け取り、その値のnull検査を書く。
4. compile拒否と、非null表明によるruntime NPEの期待を分ける。
5. 「一度読んだ値で判断したいか、最新値が必要か」から実装を選ぶ。
6. snapshotがdeep copyや大域的な並行安全性を保証しないことを説明する。

## 1. 先に予想する

次の2回の読取りは、同じ値を返すでしょうか。

~~~kotlin
if (box.value != null) {
    return box.value.length
}
~~~

box.valueを、変更可能なvar propertyと独自getterを持つval propertyに置き換えて考えてください。次に、一度だけ読んでから検査するコードと比較します。

~~~kotlin
val snapshot: String? = box.value
if (snapshot != null) {
    println(snapshot.length)
}
~~~

予想は「compileできるか」「何を何回読むか」「実行されたら何が出るか」の3つに分けます。compileできないコードに、架空のruntime結果を付けないでください。

## 2. 操作と対照を読む

ここでは実行前に固定した設計と期待を説明します。今回の実測は、この期待を変更せずに照合しました。

| 固定したcompile条件 | ソース | 期待する判定 |
|---|---|---|
| 安定したローカルvalのsnapshotと実行時の対照 | [SnapshotAndContrast.kt](src/SnapshotAndContrast.kt) | 受理。JARあり |
| var propertyをnull検査してから再読取り | [MutablePropertyRejected.kt](src/MutablePropertyRejected.kt) | SMARTCAST_IMPOSSIBLE。JARなし |
| 独自getterのval propertyを検査してから再読取り | [CustomGetterRejected.kt](src/CustomGetterRejected.kt) | SMARTCAST_IMPOSSIBLE。JARなし |

受理を期待するプログラムには、次の3経路を用意しました。それぞれ入力をAdaとnullに固定するため、実行時の期待は計6条件です。

| 経路 | Adaで始める場合の固定期待 | nullで始める場合の固定期待 |
|---|---|---|
| mutable-snapshot | 元propertyをnullへ変更しても、snapshotはAdaのまま。長さ3 | 元propertyをAdaへ変更しても、snapshotはnull。アクセス省略 |
| getter-snapshot | 最初の読取りを保存し、長さ3を使う。その後の比較用読取りはnull | snapshotはnullなので省略。その後の比較用読取りもnull |
| getter-repeated-assertion | 1回目はAdaでguardを通過。2回目はnullなので、追加した!!でNPE | 1回目がnullなのでguardで省略。2回目は読まない |

独自getterは、最初の読取りで初期値、その後はnullを返す小さなコードです。外部の並行処理や偶然の競合は使いません。getter-snapshotの2回目は、snapshotを使い終わった後の比較用読取りです。判断と利用のためにgetterを2回読むわけではありません。

固定した分類は、正常終了5条件・意図したruntime NPE 1条件・compile拒否2条件です。[保存原票](observations/operational-revision-20261006T054006019240Z/run.json)はこの分類と一致しました。期待した失敗を正常終了へ加算していません。

## 3. 条件が整った枠で再現する

今回の実行は代表1compile・1runtimeから始め、成功と資源条件を再確認して同じattemptで残りへ進みました。代表を重複実行せず、全体10.835秒、再試行0回で完了しました。[収集器](run.py)と[独立検証器](verify.py)を保存しています。実行を増やさず原票を照合する場合は次を使います。

~~~sh
python3 -B verify.py observations/operational-revision-20261006T054006019240Z/run.json
~~~

新たな実験が必要で、専有枠が許可された場合の再現コマンドは次のとおりです。



compiler・archive・javaはこのMacで前教材が使った既存の場所です。最後の「表示された実行ID」は収集器が出力するパスに置き換えます。前教材で使ったKotlin 2.4.10の既存cacheとOpenJDK 17.0.17だけを再利用します。新規インストール・SDK変更・Docker・サービス・OS設定変更は行いません。

収集器は、全体CPU idle 30%以上、1分load/論理CPU数0.75以下、メモリquery free 15%以上、free＋speculative＋inactiveの推定2 GiB以上、既知benchmark/compiler名の検出なしを確認します。単独processのCPU 25%だけでは保留しません。読取り拒否・失敗や未観測値を0件に置き換えることもありません。exec前に子processのnice実値10以上を必須とし、compiler heap最大256 MiB・runtime heap最大64 MiB、ActiveProcessorCount=1、各command最大15秒・batch枠45秒、再試行なしの逐次実行です。生成物は新しいobservations配下へ保存します。

今回の実測では11子command（版確認2件を含む）のnice実値はすべて10、timeout 0、終了後の残存owned process group 0でした。Xmxはheap上限でprocess全体の常駐メモリ上限ではなく、ActiveProcessorCountはOSの厳密なCPU quotaではありません。[資源の原票と制限](observations/operational-revision-20261006T054006019240Z/README.md)も確認してください。



## 4. 固定原典と実装をたどる

[Kotlin公式「Smart cast prerequisites」の固定版](https://github.com/JetBrains/kotlin-web-site/blob/135c79983f678c6367c5cc19eb5d8445eb3c95ce/docs/topics/typecasts.md#smart-cast-prerequisites)は、検査から利用まで値が変わらないとcompilerが判断できる条件を説明しています。var property、独自getter、ローカル変数は同じ条件ではありません。今回のローカルvalは委譲propertyではありません。

[非null表明の固定原典](https://github.com/JetBrains/kotlin-web-site/blob/135c79983f678c6367c5cc19eb5d8445eb3c95ce/docs/topics/null-safety.md#not-null-assertion-operator)も参照してください。対照コードの!!は、拒否されたsmart castを成立させる操作ではありません。再度得た値がnullなら失敗する別の操作です。

原典commitは前教材と同じ <code>135c79983f678c6367c5cc19eb5d8445eb3c95ce</code> です。[原典・分野ゴールとの対応](sources.json)、[固定期待値の全文](expected.json)、[対応範囲](COVERAGE.md)を保存しています。原典の説明・固定期待値・今回の実測原票は別々に保存しており、実測に合わせたソースや期待値の変更はしていません。

## 5. 答え合わせの観点

まずcompile受理／拒否を確認し、受理されたJARだけを実行しました。snapshot経路では、SOURCE_NOWとSNAPSHOTが違っても矛盾ではありません。一度受け取った値と、後で読んだpropertyの値を分けてください。

getterのGET#1、GET#2は原票に保存した実ログです。getter-snapshotでは先に保存した値を利用しました。getter-repeated-assertionではguard後に再読取りし、その値へ!!を適用するため、Ada入力でNPEを観測しました。

検証器は保存stdoutを全文照合し、exit、diagnostic、JAR有無も別々に確認しました。[49項目の検証結果](observations/operational-revision-20261006T054006019240Z/verification.json)を保存しています。mutable propertyの診断が並行変更の可能性を述べても、今回実際に並行変更が起きた証拠として扱いません。

## 6. 実務判断と限界

一度読んだ値を使って判定と処理を揃えたいときは、ローカルvalへの受取りが候補です。ただし、それは以後も最新の値であるという保証ではありません。処理時点の最新値や複数propertyの一貫した状態が必要なら、更新と読取りの契約を別に設計する必要があります。この教材はlock、transaction、atomic性を実証しません。

今回のString snapshotは参照の受取りです。可変object全体をdeep copyする操作ではなく、複数fieldの一括snapshotでもありません。open property、module境界、委譲property、captured local var、contract、Java境界、他compiler版、JVM以外は未検証です。全propertyや大域的な並行安全性への保証は主張しません。

現在の状態は[status.json](observations/status.json)で確認できます。有限ケースのcompiler/JVM実行・独立検証、readerの作者GUI・画像QAを完了しました。独立受入は別reviewerの記録を根拠にし、Atlas統合や共有受入数をこの作者だけで更新しません。

## 保存原票readerの確認記録

[最終GUI原票](browser-qa/run-2026-10-06T060934919Z/report.json)は、runtime 6条件とcompile拒否2条件の表示rawを元原票と照合しています。予想の一致/不一致、予想変更後の結果・答え・原票の消去、reset後の初期化、資料取得HTTP 503やdigest不一致からの復旧も確認しました。取得失敗をruntime NPEやcompile拒否として表示しません。

読み込み中にreset・条件変更・予想変更を行い、遅れて届いた旧応答で結果が戻らないことを確認しました。古い取得エラーが新条件の正常取得を消さないことも検査しています。captureは実ブラウザのreader画面で、コンパイラ実行時の画面や新たなJVM実行の証拠ではありません。[作者の画像目視](browser-qa/visual-review.json)に7枚のSHA-256と見た内容を記録しています。

初回QAはfieldset自体のPlaywright isDisabled判定で停止しました。[失敗原票](browser-qa/run-2026-10-06T060823168Z/report.json)と修正前の検査scriptを保持し、配下radioの実際の無効化を検査するよう限定修正して再確認しました。reader実装はこの再確認で変更していません。最終24項目・91操作は修正後attemptの数で、初回の8項目・38操作を混ぜていません。各attemptの専用context・profile・一時loopback serverは終了・削除済みです。
