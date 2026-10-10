# 次の1単元の具体案（未着手）

候補は「Javaの@NotNull契約と、実装が契約を破る場合を読む」です。97分野目標「23. Kotlin」のJava境界へ進み、既存の実験を再作成せず、保存証拠を読める視覚教材へつなぎます。

- 提案path：`independent-learning/kotlin-java-nullability-evidence-reader`。新git repoではない独立教材フォルダー。
- 再利用元：既存`kotlin-reference-atlas/labs/java-nullability-enhancement-process-pilot`と`evidence/diagnostics/java-nullability-enhancement-process-pilot.json`。
- 学習目的：文字列・空文字列の正常終了、Javaが@NotNullを破ってnullを返す実行時失敗、null引数のcompile拒否を分ける。annotationはJava実装の実行時保証にはならないと、この有限例から判断する。
- 操作案：各経路の結果を予想し、保存されたexit・diagnostic・照合結果を見る。Java宣言→Kotlin利用→結果の段階を図で追い、原典と実装の後で答えを開く。
- 新しいcompiler/JVM実行：不要。既存の実測を新規実験件数や独立した実行証拠として二重加算しない。

読取で確認した原票はKotlin 2.4.10 / OpenJDK 17.0.17を記録し、normalは`RESULT=5\n`、空文字列は`RESULT=0\n`に対するstdout digestと一致判定を保持します。契約違反はexit 1とNPEを含む期待との照合、null引数は`NULL_FOR_NONNULL_TYPE`・JARなしを記録しています。source 4件、固定expected、harnessの計6digestは現在のファイルと一致しました。

原票SHA-256は`8f24466df0e322257474ce6cf414f095aa09ddf21be0f035e9f832698ee732fb`です。元の原票・Lab・harnessはread-onlyで、新教材には由来とdigestを保持した参照または必要最小限の写しを置く案です。元のauthority/closure判定は変更しません。

証拠の限界も教材に残します。原票はstdout/stderr・bytecodeのdigestと判定を保存しており、全文ログ、実行日時、生成JAR/Java classの保存物は確認できません。固定期待値の文字列をdigestと照合できても「保存された実stdout全文」と呼ばず、NPEの完全なstack traceやjavap全文を再構成しません。原票記録値・期待値・コードからの説明を分けて表示します。

既存cacheの`annotations-13.0.jar`（17,536 bytes、SHA-256 `ace2a10dc8e2d5fd34925ecac03e4988b2c0f851650c94b8cef49ba1bd111478`）には`org.jetbrains.annotations.NotNull`と`Nullable`があり、固定compiler配布物内の同entryと一致しました。ただし既存pilotが使ったのは自前の最小`NotNull.java`定義です。本物のannotation jarを使った実験へ読み替えず、この橋渡しでは依存を置き換えません。

元repoのlearning/docs/README/labs内のmd/html/svg/jsonをpilot名・behavior名・class名で検索した範囲では、同pilotを読む視覚教材は確認できませんでした。この限定検索は不存在の証明ではありません。既に十分な可視化があると判明した場合は、現[COVERAGE](COVERAGE.md)に残る読取専用captureの小例へ戻し、重複制作を避けます。

これは選定案です。親担当はこの次案を承認済みですが、新path・新コード・新compiler/browser実行は未着手です。現単元の独立受入後に本制作へ進みます。
