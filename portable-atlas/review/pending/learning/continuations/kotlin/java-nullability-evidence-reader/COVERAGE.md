# 対応範囲：既存Java境界の証拠を読む

元計画は`2026-10-06/task-8/atlas-97-field-goals-ja.md`の「23. Kotlin」です。既存nullability教材に残るJava annotation境界へ進む一方、すでに存在する`labs/java-nullability-enhancement-process-pilot`を新実験として作り直しません。

| 観点 | 教材で扱う範囲 | 根拠と限界 |
|---|---|---|
| 正常な戻り値 | atlasと空文字列 | 既存runtime2条件のexit/digest/一致判定。原stdout全文は未保存 |
| 宣言と実装の違い | 自前最小@NotNullとnullを返すJava | 既存runtime失敗1条件のNPE部分一致判定。全文再検証なし |
| compile拒否 | Kotlinから@NotNull引数へnull | 保存NULL_FOR_NONNULL_TYPE・JARなし。runtime結果を作らない |
| 証拠を分ける | 原票の記録／固定期待とのdigest照合／コードの解釈 | A/B/C欄に明記。模型は実traceではない |
| 原典 | Kotlin公式固定commitのJava interop | 文書本文は複製せず参照。有限実測とは分ける |
| annotation依存 | pilotの最小定義とcache内jarを区別 | jarの存在・配布物一致は読取確認のみ。pilotの使用依存へ読み替えない |
| 制作・検査 | 小reader、説明、コピー整合40項目・表示モデル7項目 | 実GUI20検査・63操作、1280/390pxの実画像7枚を目視。独立受入はstatus、統合は未実施 |
| 取得失敗・変更後の復旧 | 欠落404・digest改変・古いsuccess/error・reset・条件/予想変更 | 保存rawの消去と新結果の保持を実DOMで確認。native再実行0 |
| 未教材 | @Nullable/JSpecify、generic型引数、他版・他platform | 今回の有限範囲から推論しない |

入口は[index.html](index.html)、対応する証拠一覧は[provenance.json](provenance.json)です。新規native実行0、共有台帳変更0です。既存pilotの実測件数を新たな実験として加算しません。既存ownerや未発見資料の不存在を主張しません。

GUI根拠は[実QA原票](browser-qa/run-2026-10-06T070916691Z/report.json)と[画像目視](browser-qa/visual-review.json)です。撮影sourceと最終sourceの差は、末尾の状態案内1行だけとして保存します。原票・固定expected・操作JSは変わっていません。最終対応は[binding](browser-qa/gui-revision-20261006T070522263097Z/final-binding.json)を参照してください。
