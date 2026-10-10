# Reboot epoch＋sequence：履歴に採ってもlatestを戻さない

固定device aの合成arrivalをPython標準ライブラリのmemory receiverで実処理する有限教材。[元IoT Subject](../../../subjects/iot-device-connectivity/README.md) README:58「data/durability」のreboot/epoch範囲だけを進めます。実device reboot・broker・通信は実行しません。

## 前提 → 読む順 → 予想

device別HWM、sequence、重複key、JSON、latestとhistoryの用途の差が前提。元device HWM→このepoch/seq identity→[key-generation CAS](../../operational-data-stores/key-generation-cas/README.md)の寿命/generation境界を読む。epochとCAS generationの具体仕様は別ですが、再利用された番号と新世代を区別する問いを共有します。

1. [事前手表](oracle.json)の各arrival key/採否/latest/historyを予想する。
2. [UI](index.html)でepoch-order→seq-only-faultの終端decision、latest epoch/seq、history件数を選び、保存した実処理と比較→答えを開く。
3. duplicate/conflict、遅延旧epoch、同seqの新epoch、同epoch内の順不同をtraceで比較する。
4. [MQTT5 §4.1 Session State](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html)を背景として読む→[receiver](receiver.py)→[独立checker](checker.py)→答えと残範囲。

## 独自契約と事前literal

**deviceに単調かつ非再利用のepochを発行できる**という独自の前提です。実epoch発行器はなく、fixtureのepoch1→epoch2だけ。epochやseqはMQTT規定/Packet Identifierではありません。arrival順は合成application到着順で、MQTT接続内wire順の主張ではありません。

identityは(device,epoch,seq)、payloadはvalueのcanonical JSON。初見の有効identityは古くてもhistoryへ追加。latestは(epoch,seq)の辞書順で大きいときだけ更新。既知identity同payloadはDUPLICATE、別payloadはCONFLICTで両状態を保持。history採用とlatest更新を別boolで記録します。

| arrival | literal key | epoch版採否 | history件数 | latest |
|---|---|---|---|---|
| a epoch1/seq4/value40 | [a,1,4] | ACCEPT_LATEST | 1 | 1/4/40 |
| a epoch2/seq1/value201 | [a,2,1] | ACCEPT_LATEST | 2 | 2/1/201 |
| 遅延a epoch1/seq5/value50 | [a,1,5] | ACCEPT_HISTORY | 3 | 2/1/201保持 |
| 同a epoch2/seq1/value201 | [a,2,1] | DUPLICATE | 3 | 保持 |
| 同a epoch2/seq1/value999 | [a,2,1] | CONFLICT | 3 | 保持 |

seq-only故障はkeyからepochを落として(device,seq)を使い、deviceのseq HWM以下の初見をSTALE_REJECTします。上のarrival2はseq1≤4で新世代を誤拒否、arrival3の旧epoch/seq5を採用してlatestが1/5へ戻ります。別対照のepoch1/seq1/value11→epoch2/seq1/value21ではkey衝突で新世代を誤CONFLICT。これは実セキュリティ認証やtransport保証の検証ではありません。

同epochでseq3→seq1の場合も初見seq1はhistoryへ採用、latestはseq3を保持します。historyは到着順、event-time sortではありません。STALE_REJECTは故障版だけで、正しいhistory方針に読み替えません。

device='a'、epochはexact int1..3、seq exact int1..99、value exact int0..999、bool不可。mode epoch/seq-only、arrival1..5。全入力を先に検査し不正epoch/seq/device/valueはREFUSED/exit2、trace空・latest/history未観測。malformed JSONは実子processexit3/stdout空のEXECUTION_FAILURE。通常duplicate/conflictはOBSERVED/exit0。

~~~sh
python3 -B runner.py --record
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py inspect
python3 -B route.py lesson
python3 -B preview.py
~~~

recordのみ新UTC runへ実command/input/exit/stdout/stderr/source hashを保存、arrival snapshotは子processstdoutから抽出した派生traceで別processではありません。[CURRENT](CURRENT)が原票を指す。旧rawを保持し通常runner/checker/routesはreadonly。各予想変更は値群を保持して旧比較・trace・answer本文を消し、答え/rawを閉じる。条件変更は予想もreset。拒否/実行失敗へ旧正常応答を補完しません。

## 独立検証 → 原典 → 答え

producer前に固定arrivalごとのkey、decision、採用history indexとlatest indexを手表で列挙。[checker](checker.py)はexpanded literalを持ち、receiverや元modelをimportしません。原票stdout/arrival snapshot・source/artifact hash・全trace/finalを照合し、8破損対照を拒否します。[QA](QA.json)は実IAB、capture、readonly SHA/mtime、資源終了を記録します。

MQTT5 §4.1 Session Stateと§4.1.1 Storing Session Stateは接続をまたぐ状態の背景locatorです。アプリ独自epoch identity・順序比較・history/latest方針はその規定ではありません。実broker、QoS、session expiry、MQTT state persistenceの適合結果にしません。

答え：seq番号だけではreboot後の新世代を区別できない。非再利用epochを仮定するならidentityと新旧比較の両方に入れ、historyへの追加とlatest更新を別に判断する。同identityのpayload変更をduplicate扱いしない。epoch発行の信頼性自体は今回の成功から推定できません。

## 残範囲

実reboot、broker、永続epoch発行とbackup復元、device認証、seq wrap、flash耐久性、receiver crash/dedup保持、実時刻/event time、複数device/外部effect、分散並行受信は未実証。[COVERAGE](COVERAGE.md)へ。Core/fullGate/commit/push/公開は割当外。全Subject完成は主張しません。
