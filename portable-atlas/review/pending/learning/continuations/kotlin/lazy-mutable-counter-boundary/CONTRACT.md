# Atlas：lazy の公開と可変カウンターの更新を分ける

この契約は実装より先に固定する。目標23のJVM・固定期待による説明を前提に、本人の委譲・スレッド安全性の問いへ対応する。対象は「SYNCHRONIZED lazy が同じ可変payloadを一度公開しても、その後の複合更新は自動で保護されない」という境界である。

## Atlas の前提と増分

既受入162件には、Kotlin lazyの初期化/公開、propertyの共有、例外/有限再入、storageの2process lost update/lock、cryptoの2thread check/use/Lock、Configの実thread snapshotがある。元Kotlin WorkbenchにもAtomicInteger増減はある。一般のスレッドやLockの初教材として扱わず、これらを前提に公開後のmutable payloadへ進む。元のcoverageや共有repoを変更しない。

各caseは新しいLazy・payload・初期化回数0・counter0から開始する。mainが固定2workerを作り、開始合図の後で両者が同じSYNCHRONIZED lazyへアクセスする。初期化関数内では待ち合わせない。両workerと終了後mainが得たpayloadを実`===`で比較し、初期化回数1、2つの異なる実thread ID、各workerの更新1回を別に確認する。

2実threadによる並行処理は、複数CPU core上で同時に命令が実行された証拠ではない。ActiveProcessorCount=1もOSの一核心固定ではない。

## Atlas の4条件と手期待

|条件|比較する更新|固定する順序|手計算の期待|
|---|---|---|---|
|plain-split|普通のIntをread、local値+1をwrite|両workerのread後にBarrier、その後にwrite|cached [0,0]、written [1,1]、final1|
|atomic-split|AtomicInteger.get、local値+1をset|同じafter-read Barrier|cached [0,0]、written [1,1]、final1|
|locked-rmw|専用lock内でread+write全体|Barrierはlock前、lock内部に待合せなし|(old,new)集合 {(0,1),(1,2)}、final2|
|atomic-rmw|AtomicInteger.incrementAndGetを1回|Barrierは更新前|返値集合 {1,2}、final2|

最初の2条件は合法の正常終了で、二人の+1が最終2へ反映されない用途上の反例である。コンパイル拒否やtimeoutを成功扱いしない。atomic-rmwのold値は別getで観測せず、今回は表示項目にしない。返値−1を説明に用いる場合も導出値と明記する。勝者workerは固定しない。

専用lockはLazyインスタンス自身ではなくpayloadが保持する別のlockである。atomic条件は内側AtomicIntegerの実参照も同じことを確認する。plain条件はatomicの値へ読み替えない。

## Atlas の同期・記録の意味

共通開始合図はLazy getterの前。反例では「両read→Barrier完了→両write」を明示的に作る。これは無制御raceの発生頻度を測らず、偶然lost updateが出るまで試行するものではない。Barrierの順序/可視性効果が加わった実行であり、CPUメモリ可視性一般の障害実験とはしない。AtomicIntegerのget/setがそれぞれatomicでも、その組合せ全体のatomic性とは別である。

修正版に同じafter-read Barrierをlock内へ置くと二人目が入れず停止するため、その配置を採らない。修正版のBarrierは複合操作より前である。worker-localなイベントを返し、Future.get後にmainで回収する。観測のための共有log lockをreadとwriteの間へ入れない。回収順や表示用の説明図をCPU全体の実行順にしない。前後関係は各workerの順序、Barrier、lock、atomic返値から説明できる部分だけを示す。

## Atlas の原典と実装

既存固定Kotlin 2.4.10/stdlibのLazy.kt、LazyJVM.ktの初期化/公開と完成値返却の本文を再利用する。JDK17のCyclicBarrier、CountDownLatch、Future、ExecutorService、AtomicIntegerとJLS17のmonitor/happens-beforeを必要箇所だけ読む。版・locator・実取得bytesのSHAをSOURCESへ記録し、索引の存在を読了としない。

## Atlas の実行条件と停止

固定Kotlin2.4.10/OpenJDK17.0.17 cacheのみ。compile1/JVM1で4caseを逐次実行、同時worker最大2、再試行0。caseごとに共通の絶対deadline2秒を設け、ready/start/Barrier/Futureは残り時間だけ待つ。失敗時は次caseを始めず、得られた部分記録と原因を保存する。所有Executorはshutdown、必要時cancel/shutdownNow、有限awaitTerminationで確認し、別に共有300ms絶対期限のjoinで実Thread終端を確認する。残存/割込は失敗とし、join(0,0)の無期限待ちは使わない。回収不能なら失敗とし、外側のJVM上限で自己process groupを回収する。

compilerはwall15秒/JVM heap256MiB/CPU soft12-hard13秒、実行はwall10秒/heap64MiB/CPU8-9秒、全体45秒を上限とする。heapは総RSS上限ではない。自分の子だけへnice>=10・CPU時間上限を設定し、実値を確認してからexec。設定不明/失敗はtarget0。

独立の実行前確認・root単独枠・fresh資源確認が揃う前に対象を起動しない。load<6、idle>=60%、memory_pressure free>=40%、利用可能推定>=2GiB、全体使用CPU=(100-idle)×CPU数<=400%（一核心100%）、既知重処理なし。ps全行/自己PID/identityの不明を0にしない。root維持browserを含む今回限定判断を正式読取に結び、前教材のPID集合/許可を流用しない。

## Atlas の受入と学習導線

実装前に作者と独立担当の手期待を分けて保存。実測の参照・thread・初期化・更新値・部分順序・完全出力/失敗/回収を照合し、少数の改変を拒否する。保存readerは予想→操作/対照→原典/実装→答え→実務判断/限界の順。rootの既存1pageで実DOM/1280・390の実viewport画像、限定Skill6問を別確認し、受入とstatus読戻しまで行う。作者はbrowser/context/page/serverを起動・終了しない。

今回は固定2worker・各1更新・4条件のJVM実行。全schedule、任意のpayload、複数fieldの不変条件、Coroutine/Flow、公平性、性能、OS競合、他platform、可視性の万能保証、正式Authority分類は対象外。元owner未確認のため統合せず、共有台帳と旧教材はread-only。
