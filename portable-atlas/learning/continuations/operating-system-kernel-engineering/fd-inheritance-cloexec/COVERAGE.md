# Atlas：FD 継承の学習範囲

正式な分野目標は `2026-10-06/task-8/atlas-97-field-goals-ja.md` 第11「OS・カーネル工学」（161–170行）、次の一歩は168行です。既存 OS の `learning/subjects/operating-system-kernel-engineering/COVERAGE.md` 9行の次1へ対応します。元のファイルと担当範囲は変更していません。

| 学べる判断 | 今回の根拠 | まだ確かめていないこと |
| --- | --- | --- |
| fork は子を作り、exec はプログラムを切替える | 親・子の PID、exec 前後の同じ PID と異なる実行コード | 全 OS・全言語 runtime |
| CLOEXEC の印は fork 直後の継承を消さない | 4 条件すべての fork 後の対象 FD | マルチスレッドからの fork |
| exec で各 FD の印が効く | on の期待 EBADF 3、off の対象保持 | FD を開く・印を変える・exec の race |
| 複製 FD の印を別々に確認する | os.dup 直後の非継承 2、元/複製の逆設定 2 条件 | C の dup 実呼出し、dup2 の同じ番号の場合 |
| 番号と参照先を区別する | 同一実行の dev/ino、全 8 バイト、設定した FD→exec 引数→子の記録→表示の対応 | 同じ inode だけから open file description の同一性を導くこと |
| 子の終了と親の参照寿命を区別する | 子を wait で回収した後の親 FD | offset の共有、socket、FD 受渡しの別方式 |
| 意図しない継承に気付く | 印 off の設定漏れ対照 | sandbox、権限設計、security 全体の保証 |

既存の pipe EOF 教材は writer の寿命と EOF、mmap 教材はメモリー可視性、unlink/replace 教材は名前と開いた参照、storage hardlink 教材は複数の名前と更新共有を扱います。今回の増分は **fork/exec の境界と、各 FD の CLOEXEC の印**です。既存内容は前提として参照し、再制作・再加算しません。元 OS 担当の現在の所有範囲・稼働は未確認です。

次の問いは、読み位置の共有を親子の明示的な同期で比較すること、C の dup と Python API の設定を別に観測すること、意図的に子へ渡す FD をどこで限定するかです。今回の図や有限結果から、offset、メモリー、性能、耐久性の確認済み範囲を広げません。

保存した実 OS 上の実験は一連の実行 1 回・4 条件、実行失敗 0、期待 EBADF 3。332 項目の照合と 10 種類の保存記録改変拒否を確認しました。GUI・実画像・独立受入の現在状態は [status.json](status.json) を参照してください。Atlas 全体への統合や OS 分野の完了は別です。

## Atlas の前提教材へ戻る

画面からは [前提教材の入口](references.html) を使えます。ローカルファイルを開ける環境では、次の元ファイルも参照できます。いずれも読取り専用です。



## Atlas の表示確認の範囲

保存結果を読む画面は 19 項目と実画像 7 枚を確認し、追加で 4 条件 × 4 時点の実 DOM 値を保存しました。[操作記録](browser-qa/run-2026-10-06T131038342Z/report.json)、[画面データの追補](browser-qa/dom-run-2026-10-06T131728851Z/report.json)、[目視記録](browser-qa/visual-review.json)へ進めます。実機のモバイル端末、他ブラウザー、Agent による Skill の案内評価は未実施です。独立受入への案内は [status.json](status.json) にまとめています。
