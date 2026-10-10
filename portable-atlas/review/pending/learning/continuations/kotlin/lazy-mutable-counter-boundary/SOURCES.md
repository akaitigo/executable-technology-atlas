# Atlas：原典と実装の範囲

固定Kotlin本文は KR-02 で取得した commit `5687445832cd835b4509b9fbc264cdf1a8201093` を再利用。Lazy.kt 54–70の初期化/公開、LazyJVM.kt 63–92の完成値返却とinitializer内同期を比較する。Lazy自身を外から同期対象にすることへの注意は同15–46行。

JDK本文は既存OpenJDK17.0.17のsrc.zipから必要範囲だけ取り出した。実archive/member/抜粋bytesのhashとlocatorは [sources.json](sources.json) に保存。これはVM binaryを逆解析した証拠ではない。

公式APIも読了：[CyclicBarrier](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CyclicBarrier.html)、[CountDownLatch](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/CountDownLatch.html)、[Future](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/Future.html)、[ExecutorService](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/ExecutorService.html)、[AtomicInteger](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/util/concurrent/atomic/AtomicInteger.html)、[JLS17.4.5](https://docs.oracle.com/javase/specs/jls/se17/html/jls-17.html#jls-17.4.5)。BarrierやFuture.getのhappens-before（前の操作が後の観測へ伝わる規則）、monitorによる排他、個別atomic操作を分ける。shutdownNowは停止を試みるだけなので期限/未回収の失敗記録も必要。

公式web本文の全byte/hashを保存したとは主張しない。ローカル抜粋は固定bytesとして [原典案内](reference.html#sources) から読める。
