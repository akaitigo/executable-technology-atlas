# Atlas：固定原典と実装の対応

Epoch は 2026-08-28。Kotlin / stdlib の固定 commit は `5687445832cd835b4509b9fbc264cdf1a8201093`、compiler は 2.4.10 です。[sources.json](sources.json) は元の取得先・固定版・実際の本文ハッシュ・行のハッシュを保存しています。今回の本文は受入済み KR-02 の bytes を再利用し、新しいネットワーク取得はしていません。

| 判断すること | 固定本文の場所 | 今回との対応 |
|---|---|---|
| 値の保持と isInitialized | [Lazy.kt](sources/stdlib-lazy.kt) 15–35 行 | 初期 false と正常終了後 true |
| delegated property からの Lazy.value | 同 43–52 行 | lazy と一般の property delegation を分ける前提 |
| 三 mode の規則 | 同 54–87 行 | PUBLICATION の呼出し回数と公開値、NONE の並行未規定 |
| mode の選択と例外の規則 | [LazyJVM.kt](sources/stdlib-lazy-jvm.kt) 15–46 行 | 例外後再試行の説明はあるが、今回の実測には含めない |
| JVM の同期初期化 | 同 63–99 行 | ロック内で再確認して一つの値を保持する |
| JVM の公開処理 | 同 102–149 行 | CAS に成功した値を保持し、他の読取りもその値を使う |

公式の固定本文は [Lazy.kt](https://github.com/JetBrains/kotlin/blob/5687445832cd835b4509b9fbc264cdf1a8201093/libraries/stdlib/src/kotlin/util/Lazy.kt) と [LazyJVM.kt](https://github.com/JetBrains/kotlin/blob/5687445832cd835b4509b9fbc264cdf1a8201093/libraries/stdlib/jvm/src/kotlin/util/LazyJVM.kt) です。CAS は「まだ未初期化なら、この値へ置き換える」という比較付きの更新です。その仕組みと、今回PUBLICATIONで保存した計算2回・返却参照1つを関連付けます。内部CASの実行そのものを追跡した記録ではなく、固定コードの読解と外からの観測を結んでいます。全ハードウェア上の動作を一回の測定で証明するものではありません。

KR-02 では固定配布物内の sources jar とこの二本文の bytes 一致も確認済みです。元索引の `libraries/stdlib/src/kotlin/util/LazyJVM.kt` は `jvm` がなく、今回の実在本文と場所が異なります。対応は KR-02 に記録済みで、元索引は変更していません。索引 metadata の hash を本文 hash に置き換えて説明しません。

[実行環境の記録](records/toolchain-readback.json)は配布 zip・launcher・JDK release・JVM library と 125 compiler ファイルを結びます。実行中の版と CPU/heap は JVM が出した環境行でも確認します。固定ソースの読解、実行コード、測定結果、正式な人の分類は別々です。
