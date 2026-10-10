# Atlas：公開規則と固定実装の読み分け

この教材は Epoch 2026-08-28、Kotlin 2.4.10 の固定 commit `5687445832cd835b4509b9fbc264cdf1a8201093` を使います。保存本文は前教材からバイト一致で再利用し、[取得元と実bytesのhash](sources/provenance.json)を残しました。索引を見つけたことと規則を読んだことを分けます。

|問い|固定本文と行|根拠が言えること|
|---|---|---|
|初期化が例外で終わった次は？|[LazyJVM.kt](sources/stdlib-lazy-jvm.kt) 15–46、19/32|次のアクセスが初期化を再試行する公開規則。副作用の巻戻しは言っていない|
|SYNC の外側の返却は？|同63–99、86–89|固定実装では関数の返却後に値を格納。再入中の内側の完了と外側の完了を別に読む|
|PUBLICATION の外側の返却は？|同102–150、122–132|関数が生成した候補と、比較交換で公開された値が異なり得る。比較交換は期待した未初期化状態のときだけ値を書き込む処理|
|NONE の代入はいつ？|[Lazy.kt](sources/stdlib-lazy.kt) 93–114、99–104|固定実装では関数の評価が終わってから代入。単一threadの今回の読解だけ|
|同じthreadのmonitorは？|[Java SE17 JLS 17.1](https://docs.oracle.com/javase/specs/jls/se17/html/jls-17.html#jls-17.1)|同じthreadは同じmonitorを重ねて取得できる。lazy再入を推奨する規則ではない|

Kotlin上流の固定本文：[Lazy.kt](https://github.com/JetBrains/kotlin/blob/5687445832cd835b4509b9fbc264cdf1a8201093/libraries/stdlib/src/kotlin/util/Lazy.kt)、[LazyJVM.kt](https://github.com/JetBrains/kotlin/blob/5687445832cd835b4509b9fbc264cdf1a8201093/libraries/stdlib/jvm/src/kotlin/util/LazyJVM.kt)。旧候補索引の `src/kotlin/util/LazyJVM.kt` には `jvm` がなく、今回の実在本文と同じlocatorではありません。元索引は変更していません。

再入の返却差は固定JVM実装の手計算です。公開APIがこの再入手順を保証した、全platformで同じ、再入が安全、と結論しません。実測前の予測は [expected.json](expected.json)、実行後の測定状態は [status.json](status.json) で区別します。
