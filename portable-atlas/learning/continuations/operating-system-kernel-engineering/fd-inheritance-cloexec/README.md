# Atlas：fork・exec の前後で FD は何を参照するか

**[操作画面 index.html](index.html)** で、CLOEXEC の印を変えた 4 条件の保存結果を読めます。fork 後には印 on の FD も残り、exec 後は印 on の FD だけが今回 EBADF になりました。親の参照は、子の終了を待った後も残っています。

教材のディレクトリで次を実行し、表示した URL を開きます。OS 実験を再実行するボタンはありません。

```sh
python3 -B preview.py
```

「条件と予想→時点再生→正常/異常比較→原典と実装→答え→限界」の順に進みます。前提は process/PID、FD、read/close/wait。FD はプロセス内の番号で、同じ番号だけを見て同じファイルと判断しません。図の矢印は保存した測定値を説明する模型です。

## この教材で分かること

1. fork の子と親は異なる PID、子の exec 前後は同じ PID である。
2. CLOEXEC の on/off は fork 直後に対象があるかという問いとは別である。
3. exec 後に残る FD と期待した EBADF を比較できる。
4. 同じファイルを指す元 FD と複製 FD に、別々の印を付けられる。
5. Python os.dup の初期設定と C の dup の契約を区別できる。
6. 設定漏れ・期待拒否・実行失敗・資料取得失敗と、親側の後片付けを分けられる。

[実装前の契約](CONTRACT.md) ／ [固定期待値](expected.json) ／ [原典](SOURCES.md) ／ [未対応範囲](COVERAGE.md) ／ [Skill](skills/atlas-fd-inheritance/SKILL.md)

## 保存した測定と確認

[実行ログ](observations/attempt-20261006T125518537210Z/run.json)は、この Mac の Python 3.9.6 で 4 条件を一連の実行 1 回、0.317 秒で実行したものです。nice 10、同時 1 子、fork/exec 各4回。全24 FD観測のうち対象保持21、期待した EBADF 3、Python dup直後の非継承2です。dev/inoは同一条件・同一実行内で比較し、大きな整数を丸めないよう十進文字列で保存しています。

[照合結果](records/verification.stdout.json)は332項目と10種類の改変拒否が成功。実子を作らない [失敗を模擬した検査](records/failure-paths.stdout.json)3件は別扱いです。通常の再確認は保存値だけを読みます。

```sh
python3 -B verify.py --run observations/attempt-20261006T125518537210Z/run.json
```

実験の完全な標準出力・標準エラーは `records/measurement-01.stdout.jsonl` / `records/measurement-01.stderr.txt`。入力・実行経路・ハッシュは [execution.json](records/execution.json)。環境読取りの最初の sandbox 準備失敗は [別記録](records/resource-read-preparation-failure.json)に残しました。同じ無害な読取りは正式な審査経路で成功し、その後の 実 OS 上の実験 1 回は成功しました。準備失敗を「実験成功」へ読み替えていません。

実行前レビューで、後片付けの無期限待機と部分ログ消失を修正しました。変更前と差分は `records/pre-run-cleanup-review/` に保存しています。観測は一連の実行で 10 秒上限、子の待機2秒、失敗時の回収待ちには別途最大1秒を設け、回収できない場合は次条件を開始しません。

GUI・実画像・別担当の受入の現在状態は **[status.json](status.json)** を参照してください。Skill 文書はありますが、Agent の案内評価を実施したこととは区別しています。

## 範囲

[元の分野目標・既存教材との対応](COVERAGE.md)に沿い、増分を FD 継承と CLOEXEC に限定しています。既存 pipe/mmap/unlink/hardlink の内容を再加算しません。元 OS 担当の現況は未確認で、元repo・他教材は変更していません。

全OS、マルチスレッドfork、offsetの共有、FDのrace、性能、メモリー、電源断後の耐久性は未検証です。同じdev/inoだけで「開いた参照」全体の状態を共有すると実証したわけでもありません。新規実測は別の明示操作 `experiment.py --record` であり、画面と通常検証は保存記録だけを読みます。Atlas全体の統合・OS全体の完了は主張しません。

## Atlas の画面確認

[初回の操作確認](browser-qa/run-2026-10-06T131038342Z/report.json)は 19 項目、実ポインター 77 操作、入力 11 回。幅 1280 / 390、予想・条件の変更、リセット、資料取得失敗と改変、遅れた成功・失敗応答の扱いを確認しました。[実画像 7 枚の目視記録](browser-qa/visual-review.json)も保存しています。

初回記録には照合の成否だけが残り、16 時点の表示値自体が不足していました。そのため [画面データの追補](browser-qa/dom-run-2026-10-06T131728851Z/report.json)で、4 条件 × 4 時点の実際の表、図、表示 JSON、ボタン状態を保存しました。追補は 23 ポインター操作・入力 4 回で、OS 実験や画像撮影は追加していません。両方とも nice 10・45 秒上限で実施し、自己所有のブラウザー・プロファイル・配信サーバーを終了しています。

[資料の最終照合一覧](records/final-binding.json)は状態記録を除く保存ファイルのハッシュを結びます。別担当の受入結果への案内は、可変の [status.json](status.json) に記載します。Atlas 全体への統合は未実施です。
