# Javaの@NotNull契約を、保存証拠から読む

入口は[index.html](index.html)です。Javaが通常の文字列・空文字列・nullを返す場合と、Kotlinがnull引数を渡す場合を比べます。正常終了、実行時失敗、compile拒否を、起きた段階で読み分ける教材です。

既存`kotlin-reference-atlas`の`java-nullability-enhancement-process-pilot`を視覚教材へつなぎます。新しいnative実験は行いません。元原票・期待値・4 source・収集コードの7ファイルを、digestを保持してこのフォルダーへ写しました。元repoは変更していません。[由来](provenance.json)と[制作状態](observations/status.json)を参照してください。このreaderのGUI操作・実画像の目視を完了しました。独立受入は作者QAと分けて状態記録へ記載し、Atlas統合は未実施です。

## 到達目標

1. Javaの@NotNull宣言と、その実装が返す値を分ける。
2. 空文字列をnullと区別し、長さ0を正常な値として読む。
3. Kotlinのnull引数拒否と、Javaの契約違反による実行時失敗を区別する。
4. 保存された記録、固定期待値との照合、コードからの説明を分ける。
5. digestだけから失われたログ全文を復元できるとは考えない。
6. この有限例を全annotation・全compiler版の保証へ広げない。

## 1. 予想する

Javaの`@NotNull String violatesContract()`が実際には`null`を返します。Kotlinから`JavaNulls.violatesContract().length`を使った場合、compileで拒否されるか、実行時に失敗するか、正常終了するかを予想します。

次に、同じAPIが`"atlas"`や`""`を返す対照と、`@NotNull`引数へKotlinから`null`を渡す拒否例を比べます。画面で予想を選ぶまで答えは表示しません。条件・予想の変更やresetでは、前の結果・原票表示・答えを消します。この動作は今回の実ブラウザ検査で確認しました。

## 2. 保存証拠を読む

このフォルダーで次を実行し、表示された127.0.0.1のURLを開きます。port 0は空きportを選びます。終了時はCtrl+Cで自分のserverを停止してください。

~~~sh
python3 -m http.server 0 --bind 127.0.0.1
~~~

画面のボタンは[元原票の写し](evidence/evidence/diagnostics/java-nullability-enhancement-process-pilot.json)と[固定期待値](evidence/labs/java-nullability-enhancement-process-pilot/expected.json)を取得し、両ファイルのSHA-256を固定値と照合します。Kotlin・Java・javac・javapは起動しません。全4経路を同じ画面の表で比べます。

| 経路 | 元原票が保存したこと | このreaderで確認できること |
|---|---|---|
| 通常の文字列 | runtime exit 0、stdout期待との一致判定・digest | 固定期待`RESULT=5\n`のdigestが保存digestと一致 |
| 空文字列 | runtime exit 0、stdout期待との一致判定・digest | 固定期待`RESULT=0\n`のdigestが保存digestと一致 |
| 契約を破る戻り値 | runtime exit 1、NPEを含む部分文字列への一致判定 | 保存判定を読む。失われたstderr全文をこの場で再照合することはできない |
| null引数 | compile exit 1、NULL_FOR_NONNULL_TYPE、JARなし | 固定diagnosticと保存IDの一致。拒否されたソースのruntimeはない |

画面のA欄は元原票の値、B欄は固定期待との対応、C欄はソースと記録からの説明です。正常2経路では期待文字列のdigestをreaderでも計算します。その一致を「保存stdout全文の再生」と呼びません。NPEの完全なstack trace、javap出力、実行traceを生成・復元していません。

## 3. 原典と実装へ進む

[Kotlin公式の固定原典](https://github.com/JetBrains/kotlin-web-site/blob/135c79983f678c6367c5cc19eb5d8445eb3c95ce/docs/topics/jvm/java-interop.md#nullability-annotations)は、Javaのnullability annotationをKotlinのnullable/non-nullable型へ対応させる説明です。この説明と、今回保存された有限例を分けて読みます。

実装は[JavaNulls.java](evidence/labs/java-nullability-enhancement-process-pilot/java/pilot/JavaNulls.java)、[Kotlin利用側](evidence/labs/java-nullability-enhancement-process-pilot/kotlin/JavaNullabilityBoundary.kt)、[拒否例](evidence/labs/java-nullability-enhancement-process-pilot/kotlin/RejectedNullArgument.kt)にあります。画面のコードは修飾子を省略した説明用抜粋です。

元pilotは[最小NotNull.java](evidence/labs/java-nullability-enhancement-process-pilot/java/org/jetbrains/annotations/NotNull.java)をローカルで定義しています。既存固定compiler cacheの`annotations-13.0.jar`にもNotNull/Nullable classがあることを読取で確認しましたが、それはこのpilotがそのjarを使った証拠ではありません。依存の差替えや実行のやり直しはしていません。

[元収集コードの写し](evidence/scripts/run_java_nullability_enhancement_process_pilot.py)は保存判定を解釈するための参照資料です。この教材フォルダーで実行するrunnerではありません。原票のbytecode判定はjavapテキスト内の呼出し順・文字列の有無を調べています。命令列全体やすべての制御経路を独立に証明したものではありません。

## 4. 答えと実務判断

空文字列はnon-nullな値で、長さ0は正常な結果です。一方、`@NotNull`宣言を付けたJava実装も、コードとしてはnullを返せます。このpilotの利用側は戻り値のlengthを読み、原票はNPEを含む実行時失敗を記録しています。Kotlinからnull引数を渡したソースのcompile拒否は、これとは別の段階です。

外部APIを使うときは、型の契約と、提供側の実装が契約を守るかを別々に確認します。この証拠だけで全annotation・全ライブラリ・全compiler版について判断しません。

## 5. 軽い整合確認と残項目

元repoの実行環境を必要とせず、保存コピーのハッシュと固定値を確認できます。

~~~sh
python3 -B verify.py
node check-model.mjs
~~~

いずれもKotlin/JVM・ブラウザを起動しません。Pythonは元原票と写しの対応を、Nodeは4経路の表示用データと拒否条件を検査します。結果は[証拠整合](observations/data-verification.json)と[表示モデル検査](observations/model-verification.json)に保存します。これらは実DOM操作・画面目視・独立受入の代用ではありません。

別に行った[実ブラウザ検査](browser-qa/run-2026-10-06T070916691Z/report.json)は20検査・63回の実ポインター操作・7実captureです。1280pxと390pxで4条件の表示raw・比較表を元JSONと照合し、欠落404・改変digest・古い遅延success/error・条件や予想変更・reset後の結果消去と復旧を確認しました。[保存画像の目視記録](browser-qa/visual-review.json)と[最終binding](browser-qa/gui-revision-20261006T070522263097Z/final-binding.json)を参照できます。ブラウザ・専用profile・自分のloopback serverはすべて終了・削除済みです。

captureはGUI検査時点の実画面です。撮影後、末尾の古い「GUI未実施」を現在状態への参照に変える1行だけを更新しました。撮影時sourceと[文面差分](browser-qa/gui-revision-20261006T070522263097Z/post-capture-footer.diff)を保持し、画像をその更新後のcaptureと扱いません。学習本文・操作コード・元証拠は不変です。

原票に元の実行時刻、stdout/stderr全文、javap全文、生成JAR/classはありません。`provenance.json`の時刻は今回の写しを作った時刻です。元のnative実行日時として扱いません。JSpecify、@Nullableの対照、generic型引数、他compiler版、他platformは未教材です。原票のauthority/closure判定や共有受入数は更新していません。
