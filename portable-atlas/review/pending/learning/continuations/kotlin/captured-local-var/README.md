# Kotlin：捕捉されたlocal varのsmart cast境界

入口は[保存原票を読む操作画面](index.html)です。書換前に保存した値と、ラムダが変えた現在の値を比べ、compile拒否と正常なnull分岐を区別できます。

制作状態：固定Kotlin 2.4.10 / OpenJDK 17.0.17でcompile 2条件・runtime 4条件を実行し、[独立検証46項目](observations/20261006T062456931814Z/verification.stdout.json)が通過しました。2026年10月6日15:24:59–15:25:08 JST、1batch 8.949秒です。受理1・期待したcompile拒否1・正常runtime 4を分離しています。この単元のGUI操作と保存7画像の目視も完了しました。別reviewerによる独立受入とAtlas統合の状態は[現在の状態](observations/status.json)で確認してください。

[実行原票](observations/20261006T062456931814Z/run.json)と[要約](observations/20261006T062456931814Z/summary.json)を保存しています。実行前に書いた固定期待値・ソース・検証器を変更せず照合しました。コンパイラ枠は終了・解放済みです。

前教材[smart castが成立する境界](../kotlin-smart-cast-boundaries/README.md)では、propertyの再読取りとローカルvalを比較しました。今回はローカル変数の中でも、書き換えるラムダに捕捉されたvarを比べます。既存のInt加算のcapturedClosure Labやsealed型のsmart cast例は存在しており、それらを今回の検証済み条件へ数え直しません。

## 到達目標

1. 変更のないlocal varと、書換ラムダが捕捉したlocal varを区別する。
2. null検査後に同じ変数を使う際、検査時の値が保たれるか考える。
3. 一度受け取ったlocal valと、後で変更された変数の値を分ける。
4. compile拒否と、実行時の正常なnull分岐を別に照合する。
5. 以前の値を使うか最新値が必要かから、実装の意図を決める。
6. この有限例を全ラムダ・inline/contract・並行安全性へ一般化しない。

## 1. 予想する

次はcompileできるでしょうか。`mutate()`を呼ぶ直前と直後で、localの値が変わり得ることに注目してください。

~~~kotlin
var local: String? = initial
val mutate: () -> Unit = {
    local = if (local == null) "Ada" else null
}
if (local != null) {
    mutate()
    return local.length
}
~~~

予想を「compileが受理されるか」「実行できた場合に何を使うか」に分けます。compile拒否を期待するソースに、架空のJVM出力を付けないでください。[保存原票reader](index.html)で条件と予想を選び、保存した結果を比較できます。画面の流れは模式図で、実行traceではありません。readerはKotlinやJVMを起動せず、固定run.jsonとexpected.jsonを取得してSHA-256を照合します。

画面を使うには、この教材フォルダーで次を起動し、表示された127.0.0.1のURLをブラウザで開きます。port 0は空きportを選びます。終わったらCtrl+Cで自分のserverを終了してください。

~~~sh
python3 -m http.server 0 --bind 127.0.0.1
~~~

条件と予想→保存原票を読む/正常・異常の対照→原典・実装→予想と照合する/限界、の順に進めます。比較表では正常終了という分類だけでなく、CONTROL_FINAL、SNAPSHOT、CAPTURED_NOW、RESULTを読み、同じ結果3でも使った値がどの時点のものかを区別してください。

[GUI検査原票](browser-qa/run-2026-10-06T064513392Z/report.json)では、1280pxと390pxで21検査・78回の実ポインター操作・7枚の実captureを保存しました。全4runtimeと拒否1条件の表示rawを原票と照合し、予想や条件の変更、reset、HTTP 503、digest不一致、遅延した古いsuccess/errorからの復旧と結果の消去を確認しています。[画像の目視記録](browser-qa/visual-review.json)も参照できます。検査中にKotlin/JVMは再実行せず、終了後は自分のブラウザ・profile・loopback serverをすべて終了・削除しました。

## 2. 操作と正常な対照を読む

| 条件 | 操作 | 固定期待と一致した実測 |
|---|---|---|
| local-control | 捕捉されず、検査から利用まで変更しないlocal varを読む | Adaは長さ3、nullは利用を省略 |
| captured-write-rejected | 書換ラムダを呼んだ後、検査したlocal varへ直接lengthを呼ぶ | SMARTCAST_IMPOSSIBLE。JARなし、runtimeなし |
| captured-snapshot | ラムダを呼ぶ前にlocal valへ受け取り、保存値を検査して利用する | Adaを保存した場合は3、nullを保存した場合は利用を省略 |

accepted側の[CapturedLocalVar.kt](src/CapturedLocalVar.kt)には2経路があります。それぞれAda/nullを与えた4条件はexit 0・空のstderrで正常終了しました。[CapturedWriteRejected.kt](src/CapturedWriteRejected.kt)は別ファイルで、exit 1・SMARTCAST_IMPOSSIBLE・JARなしを観測しました。拒否されたファイルをJVMで実行していません。

snapshot経路は`CAPTURED_INITIAL`→`SNAPSHOT`→`MUTATION_APPLIED`→`CAPTURED_NOW`→`RESULT`の順に出力しました。ラムダはその場で明示的に1回呼びます。別threadや非同期処理は使いません。Adaを保存した後にlocalをnullへ変えても、保存したsnapshotを最新値として読み替えないでください。

~~~text
CAPTURED_INITIAL=Ada
SNAPSHOT=Ada
MUTATION_APPLIED
CAPTURED_NOW=<null>
RESULT=3
~~~

これは今回の`captured-snapshot / ada`から抜き出した実stdoutです。null入力では書換後のlocalがAdaになっても、先に保存したsnapshotはnullのため`RESULT=SKIPPED`でした。固定期待値の説明図と、取得したこの実ログを区別してください。

## 3. 許可された枠で再現する

[run.py](run.py)は前教材で使った既存Kotlin 2.4.10配布物とOpenJDK 17.0.17を再利用します。新たなinstall・SDK変更・Docker・OS設定変更は行いません。

保存した今回の結果だけを確認する場合は、次でKotlinやJVMを追加起動せず検証できます。

~~~sh
python3 -B verify.py observations/20261006T062456931814Z/run.json
~~~

新たに実行が必要で、専有枠を調整した場合の再現手順は次のとおりです。



実行前と代表1compile・1runtimeの後に、全体CPU idle 30%以上、1分load/論理CPU数0.75以下、メモリquery free 15%以上、free＋speculative＋inactiveの推定2 GiB以上、既知benchmark/compiler名の検出なしを確認します。推定値は直ちに確保できる量の保証ではありません。読取不能を0件とみなさず、単独daemonのCPU値だけで保留もしません。実行枠は親担当がFlutterなどと直列化します。

全commandはexec前に自分の子processのnice実値10以上を確認します。compiler heap 256 MiB・runtime heap 64 MiB、ActiveProcessorCount=1、各command 15秒・batch 45秒上限、逐次1batch・再試行0回です。Xmxはheapの上限でRSS全体の上限ではなく、ActiveProcessorCountもOSの厳密なCPU quotaではありません。代表を重複実行せず、資源条件が保たれた場合だけ残りへ進みます。

今回の[開始前ゲート](observations/20261006T062456931814Z/resource-gate.json)はload 7.76 / 12CPU、CPU idle 52.12%、メモリquery free 45%、回収可能量推定5.40 GiBでした。[代表実行後](observations/20261006T062456931814Z/resource-gate-after-representative.json)もload 7.69、idle 64.5%、メモリ42%・推定5.09 GiBで条件を満たしました。既知の重処理は両時点とも0件でしたが、未知の処理の不存在や将来の余裕を保証する数値ではありません。

版確認2件を含む8子commandはnice実値がすべて10、timeout・再試行・終了後の残存owned process groupはすべて0でした。固定archive/launcherのdigestと展開済み125ファイルを照合しています。旧教材・OS・他process・保護対象DeepSeekUIの設定は変更していません。

## 4. 固定原典と実装で確かめる

[Kotlin公式の固定版「Smart cast prerequisites」](https://github.com/JetBrains/kotlin-web-site/blob/135c79983f678c6367c5cc19eb5d8445eb3c95ce/docs/topics/typecasts.md#smart-cast-prerequisites)は、local varについて検査と利用の間の変更や、変数を変更するラムダによる捕捉を条件に挙げています。同じ文書の[Inline functions](https://github.com/JetBrains/kotlin-web-site/blob/135c79983f678c6367c5cc19eb5d8445eb3c95ce/docs/topics/typecasts.md#inline-functions)には別の分析を利用する場合も説明されています。

今回の例から「捕捉されたら常にsmart castできない」「ラムダを使えば必ずNPEになる」とは言えません。変更するラムダを明示的に呼ぶ、この固定コードの受理/拒否を確かめる教材です。[原典と既存教材の対応](sources.json)、[変更前に固定した期待値](expected.json)を保存しています。

## 5. 答え合わせと実務判断

まずcompileのexit・diagnostic・JAR有無を確かめました。拒否されたソースはJVMで実行しませんでした。受理されたJARについてだけ、4条件のstdout全体・exit 0・空のstderrを[独立検証器](verify.py)で固定期待値と比較しました。今回はruntime NPEを期待するケースを設計しておらず、観測したNPEも0件です。

拒否診断は`CapturedWriteRejected.kt:9:16`の`local.length`に対応し、書換えを行うclosureに捕捉されたlocal変数であることを指摘しています。このcompile拒否を「nullを実行してNPEが起きた」と読み替えないでください。

一度読んだ値で判断を揃えたい場合は、書換前にlocal valへ受け取る方法を検討できます。呼出し後の最新値を使う必要があるなら、先に保存したsnapshotが要件に合うとは限りません。nullなら処理を省略することも、今回の契約に沿った正常な分岐です。

## 6. 限界

これはString参照と明示的な逐次変更の小例です。全capture、読取専用capture、inline/callsInPlace、contract、委譲local、ラムダのescapeや保持期間、別threadとの競合、JVM以外、他compiler版は未検証です。deep copy・複数変数のatomic snapshot・大域的な並行安全性も示しません。

実compile/runと保存原票の独立検証、この単元のGUI操作・画像QAを完了しました。別reviewerによる独立受入は作者QAと分けてstatusに記録し、Atlas統合は未実施です。[COVERAGE](COVERAGE.md)に有限範囲を記録し、この単元をKotlin全体の完成とは扱いません。前教材smart-cast readerのGUI・画像QA・独立受入PASSを、この新単元の実施済み件数へ転用しません。
