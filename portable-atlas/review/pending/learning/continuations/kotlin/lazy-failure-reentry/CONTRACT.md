# Atlas：lazy の例外後の再試行と、初期化中の再入

この契約と `expected.json` は実装・実測より先に固定します。専有先はこのディレクトリだけです。元 Kotlin repository、前教材、受入記録、共有台帳は読取り専用で、元の共有担当者の現況は未確認です。

## Atlas の到達点と前提

初期化関数が例外を投げた後の次アクセスと、初期化中に同じ Lazy を読む再入を区別する。呼出し回数、生成した値、getter が返した参照、後の読取り、`isInitialized()` を混同しない。前提は関数値、例外と try/finally、Lazy、`===`（同じインスタンスかの比較）、main thread での逐次実行です。

[分野目標23](../../../../2026-10-06/task-8/atlas-97-field-goals-ja.md)と、[前教材の未対応範囲](../kotlin-lazy-mode-boundaries/COVERAGE.md)に対応します。前教材の逐次成功・並行2読取りを再制作しません。今回は単一 main thread の6条件で、worker は作りません。

## Atlas の固定根拠

Epoch 2026-08-28、Kotlin 2.4.10、stdlib commit `5687445832cd835b4509b9fbc264cdf1a8201093`。前教材に保存された実本文を再利用し、実bytesの SHA-256 を記録します。

- `LazyJVM.kt` 15–46、特に19/32：例外後、次のアクセスが初期化を再試行する公開規則。
- 同63–99：SYNCHRONIZED は初期化関数から返った値を格納する。
- 同102–150：PUBLICATION は未初期化値への比較交換に勝った値を公開する。
- `Lazy.kt` 93–114：NONE の固定 JVM 実装の格納順。
- [Java SE17 JLS 17.1](https://docs.oracle.com/javase/specs/jls/se17/html/jls-17.html#jls-17.1)：同じ thread による monitor の再取得。これは lazy 再入の API 保証ではありません。

本文索引の存在や locator 文字列のhashを、本文の意味読了としません。旧候補 `libraries/stdlib/src/kotlin/util/LazyJVM.kt` と実在本文 `libraries/stdlib/jvm/src/kotlin/util/LazyJVM.kt` の差を保持します。

## Atlas の実装前6条件

すべて新しい Lazy で始め、Token の marker は7です。Token の id は initializer の呼出し番号で、生成順ではありません。

|条件|mode|先に固定した期待|
|---|---|---|
|failure-synchronized|SYNCHRONIZED|最初の読取りで専用例外、次はToken2、再読も同じToken2。呼出し回数0→1→2→2、初期化済みfalse→false→true→true|
|failure-publication|PUBLICATION|同じ逐次入力・同じ期待。並行例外への保証には使わない|
|failure-none|NONE|同じ逐次入力・同じ期待。並行安全性には使わない|
|reentry-synchronized|SYNCHRONIZED|内側Token2、外側が別Token1を生成。外側getterと後のgetterはToken1で同じ参照|
|reentry-publication|PUBLICATION|内側Token2、外側が別Token1を生成。外側getterと後のgetterはToken2で同じ参照|
|reentry-none|NONE|内側Token2、外側が別Token1を生成。外側getterと後のgetterはToken1で同じ参照|

例外条件は、呼出し1で `PlannedInitFailure("Atlas planned first initialization failure")` を投げ、呼出し2で成功します。専用例外だけを期待された異常として記録し、type/message/stack を保存します。予期しない例外や期待例外の不発は実験失敗です。

再入条件は、外側が呼出し番号1をローカル変数へ固定してから同じ Lazy を一度だけ読みます。内側は番号2を固定してToken2を返し、外側はその後に別のToken1を生成・返却します。実際の生成順は2→1です。深さは最大2、3階層目に入った場合は再アクセスより前に専用の深さ制限例外で停止します。finally で深さを戻します。

内側のgetter返却、外側が作った値、外側initializerの返却、外側getter返却、後のgetter返却を別に保存します。`inner === outerCreated` はfalse、`later === firstGetter` はtrue。SYNC/NONEでは `firstGetter === outerCreated` がtrue、PUBLICATIONでは `firstGetter === inner` がtrueと予測します。全modeで呼出し2回、最大深さ2、終了深さ0。初期化状態は初期false、内側getter終了後true、外側終了後true、後の読取り後trueです。内部の非公開cacheを直接見たとは主張しません。

## Atlas の実行と失敗の保存

既存 Kotlin 2.4.10 / OpenJDK17.0.17 cacheだけを使用。compile1回・JVM1回・再試行0、一つのJVMで6条件を逐次実行します。各条件の境界と事象を JSON 行で逐次出力し、中断してもそれまでの完全行と未完のstdout/stderrを保持します。想定外の失敗なら次条件を始めません。無制限再帰や StackOverflow を起こす実験はしません。

root の専有枠付与後、fresh load<6・idle25%以上・memory query空き20%以上・推定空き2GiB以上・既知重処理/他headlessなしを確認。読取不明を0としません。自己processのniceを10以上に設定し実値を確認したlauncherだけがexecします。失敗時は対象を開始しません。CPU1、compiler heap256MiB/runtime64MiB、compiler15秒/runtime10秒、全体45秒。自己所有groupだけTERM後0.5秒、必要ならKILL後最大1秒回収。回収不能は失敗として後続を止めます。対象起動・exec試行・未到達を区別します。

新SDK、install、OS/daemon設定変更、外部サービス、Docker変更、公開、commit/pushはしません。

## Atlas の教材と受入

予想→条件/時点の操作→正常/期待例外の比較→原典/実装→答え→限界の順に読む画面を作ります。矢印図は保存測定結果を説明する模型で、実画面の画像とは区別します。6条件×4時点の実DOM値と1280/390の実画面、前/次の両方向、予想/条件/resetでの消去、資料取得失敗/改変/古い応答を有限に確認。browserは別の専有枠で自己profile/serverを回収します。

限定Skillは保存結果の読取と新しい実測を分け、未実測なら規則/手計算/コードの読取で止まります。固定期待値・入力hash・実行環境・完全stdout/stderr・終了回収・実DOM/画像・案内の少数読取を別担当が確認します。APIの例外再試行と固定実装に依存する再入を一つの保証へ広げません。正式Authority分類、一般Agent能力評価、元repo統合、教材数加算はこの作者の受入に含めません。

未対応：並行する例外、threadを跨ぐ再入、複数Lazy間の循環、外部lock、無制限再帰、性能、他platform、一般property/class委譲。次の不足をCOVERAGEへ残し、OS/Kotlin全体の完了とは呼びません。
