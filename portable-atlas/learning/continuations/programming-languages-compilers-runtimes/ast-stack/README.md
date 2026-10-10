> 配布用保存reader：端末・実行管理情報を除いた観測データを、専用のschemaとSHAで照合して再生します。元原票のSHAと区別しています。新しい計算・GUI検証ではありません。[データの由来と復元](MIGRATION.md)を確認してください。

# Atlas：AST から stack 命令へ

`2 + 3 * 4` の構文木を、`CONST 0 / CONST 1 / CONST 2 / MUL / ADD` へ写します。括弧を付けると何が変わるか、定数表の index は何を指すか、命令ごとに stack がどう変わるかを追う教材です。

**CLI の実測・保存値検査と、正常5式・意図した拒否7条件の画面操作検査を行いました。** 最新の別担当確認は [状態記録](status.json) の受入参照から辿れます。

## Atlas の読む順

1. [実装前の契約](CONTRACT.md) で、整数・加算・乗算・括弧と3命令の範囲を読む。前提は文字列→AST→再帰的な木評価です。
2. [固定入力](inputs.json) から `2 + 3 * 4` と `(2 + 3) * 4` を選び、命令順と各 stack を予想する。stack の右端が頂点です。
3. [手計算](HAND_TRACE.md) と [固定期待値](expected.json) を対照に、[保存した実行結果](observations/attempt-20261006T180030750576Z/run.json) の `records` 内の条件を読む。正常5式と意図した拒否7条件を分けています。
4. [原典対応](SOURCES.md) → [変換器と VM](compiler_vm.py) → [既存の木評価器](inputs/prerequisite-language.py) へ戻る。
5. 答えを値だけで判定せず、node の左右・命令の出所・定数 index・各命令前後の stack まで比べる。[今回の範囲と次の問い](COVERAGE.md) へ進む。

到達目標は、AST の各 node がどの命令範囲に対応するか説明すること、括弧の Group が命令を増やさず木の形を変えると説明すること、定数の重複除去と命令数を区別すること、木評価と VM の経路を分けること、VM の拒否と実行失敗を区別すること、値の一致だけでは順序を保証できないと判断することです。

## Atlas の画面入口

[index.html](index.html) に条件・予想→時点操作→原典とコード→答え→限界の画面を用意しました。図は保存値から作る説明模型で、撮影した画像ではありません。画面は `data.js` に元 JSON の正確なテキストを同梱し、通信や Python の起動をせず読む設計です。

今回確認した入口は、同じディレクトリのファイルをHTTPで配信した `index.html` です。単一の既存ブラウザー内で1280/390の表示と操作を確認しました。`file:` での直接表示は未確認です。既存の配信入口がない場合はテキストとJSONを利用でき、閲覧のための再計算は不要です。[画面確認の範囲](GUI_VERIFICATION.md)を参照してください。

画面の予想は自由記述で自動採点しません。予想・条件・リセットの変更で古い結果を消し、SHA-256 の処理が遅れて戻っても世代が違えば捨てる設計です。資料欠落・改変は資料の読込み失敗として表示し、意図した VM の拒否と混同しません。これらの操作は保存結果を使う実DOM検査でも確認しました。先の模型検査と実画面の記録は分けて保持しています。

## Atlas の実行ログと再確認

2026-10-06 18:00:30 UTC に、既存 Python 3.9.6 / macOS arm64 で一連の実行1回を行いました。正常5式の値は **14、20、26、0、6**。VM の意図した拒否は7条件で、Python 自体の予期しない失敗は0件です。対象子1、worker0、再試行0、nice 実値10、CPU 上限2秒・経過時間上限3秒、終了後に自己所有子を回収し process group の不在を確認しました。全手順の記録は約0.128秒です。

- [完全な実行記録](observations/attempt-20261006T180030750576Z/run.json)、[標準出力全文](observations/attempt-20261006T180030750576Z/producer.stdout.txt)、[標準エラー](observations/attempt-20261006T180030750576Z/producer.stderr.txt)、[優先度確認](observations/attempt-20261006T180030750576Z/producer.priority.json)
- [実行前の資源読取](records/resources-20261006T180004981879Z.json)：load 3.71/12 CPU、idle 84.9%、メモリ空き照会51%、推定6.08 GiB。推定量は使用可能量の確保保証ではありません。
- [固定入力11件の hash](records/pre-execution-inputs.json) と実行記録の前後一致、[保存値検査246項目・改変8件の拒否](records/verify.stdout.json)
- [データ同梱の対応](records/data-binding.json)：同梱文字列の hash と元ファイルの byte hash は別に照合します。
- [画面コードの模擬検査178項目](records/reader-model.stdout.json)：Node の小さな要素模型を使った検査で、ブラウザーの実 DOM や描画の証拠ではありません。[検査コード](reader-model-check.cjs) は `node reader-model-check.cjs` で保存データだけを読みます。初回の検査コード構文ミスと、2回目の模擬データ削除方法の誤りは [初回記録](records/model-attempt-1/failure-note.json) と [2回目記録](records/model-attempt-2/failure-note.json) に保持しています。

このディレクトリで、既存結果の再検査だけを行うコマンドです。実験の子は新しく起動しません。

```sh
python3 -B verify.py --run observations/attempt-20261006T180030750576Z/run.json --mutations
```

保存結果の閲覧に再実行は不要です。再実行時は、[契約](CONTRACT.md) の資源条件・排他調整・優先度・時間制限を確認し、`resources.py` の新しい記録を `run.py --execute --resource-record <その記録>` へ渡します。既存記録を上書きせず、読取不明・起動前停止・実行失敗を区別します。実 DOM・画像の確認状態は実測の再確認と分け、最新の状態記録へ残します。

## Atlas の判断の境界

この VM は Python 整数と JSON 配列の独自命令です。書籍の C/double/バイト符号化、実機の命令、Lox との互換性を実装したものではありません。最終値が同じでも、左右の順序・命令数・最大 stack 高が正しいとは限りません。任意の入力の安全性、構文エラーの全範囲、変数・関数・最適化・性能は今回の実測から結論しません。

元リポジトリの共有編集者は現在未確認です。前提のコードは完全一致コピーを使い、元の教材・受入記録・全体台帳を変更していません。今回の作者による教材数加算は0です。
