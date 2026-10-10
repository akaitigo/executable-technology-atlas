# 対象と未教材

有限2テストの全2順序×共有/fixtureの4条件。各条件2回の実unittest child process、state前後・assertion・runner outcome・exit・生stdout/stderrを扱います。13入力拒否、UIreset/旧応答拒否、独立手表を照合します。

未教材: OSスケジューラ、thread並列、race、実CI、外部I/O・DB・ファイル共有、cache invalidation一般論、test suite巨大集合、ランダム時刻、flaky発生確率、pytest実行、実timeout/error誘発、全ブラウザ/アクセシビリティ。

最初に0へ初期化した子process内での順序依存です。2回再現を確率の証明と呼びません。fixture方式を他の共有外部資源まで自動保証すると扱いません。失敗をskip/xfailに置き換えず、assertionと失敗原票を残します。Software Quality/Core全体の完成は主張しません。
