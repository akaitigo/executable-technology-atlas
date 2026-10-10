# Atlas：この単元の確認範囲

正式な到達目標は[第23 Kotlin](../../../../2026-10-06/task-8/atlas-97-field-goals-ja.md)。[KR-02の概念](../kotlin-delegation-concept-map/README.md)と[前のmode教材](../kotlin-lazy-mode-boundaries/COVERAGE.md)が残した、例外・再入の問いに対応します。元の専用検証課題全体の完了には換算しません。

|対象|この単元の有限範囲|まだ言えないこと|
|---|---|---|
|例外後の再試行|3mode、main thread、初回専用例外→成功→再読|副作用の巻戻し、並行例外、全例外型|
|再入|3mode、最大深さ2、inner2→outer1の生成、各返却参照|一般API保証、thread間循環、外部lock、無制限再帰|
|値と参照|id/markerと実際の`===`を別保存|id一致だけからidentityを証明すること|
|固定原典|LazyJVM/Lazy実本文、版・行・hash|本文索引だけで正式意味分類を完了したとすること|
|学習画面/Skill|保存結果へ案内する有限操作と読取|未知の質問全般やAgent一般性能|

実測・実画面・受入の実施状況は [status.json](status.json) を参照。未実測の手計算は [expected.json](expected.json) に分離し、実測で期待を書き換えません。

Atlas の次の問いは、初期化関数の副作用を再試行可能にする設計です。並行例外、複数Lazyの循環などを勝手に今回へ追加しません。他platform・性能・一般委譲は未対応として残します。作者の教材加算は0、最終の重複照合は全体担当が行います。

Atlas 実測の増分は今回の6条件のみ。compile/JVM各1回、期待された初期化例外3件、guard到達0、再入深さ2、worker0。前教材の成功・並行条件は再実行していません。実画面と別担当の受入は別工程です。

Atlas の画面は6条件・24時点を実DOMで照合し、1280/390の画像を保存しました。[画面確認の記録](GUI_VERIFICATION.md)と別担当の受入は状態記録へ分けます。保存実測の独立115照合、限定Skillの5問、画面検査を一般Agent評価へ換算しません。
