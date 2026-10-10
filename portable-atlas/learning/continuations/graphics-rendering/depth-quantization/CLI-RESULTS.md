# Atlas — 保存した奥行き計算

今回の有限計算は [実行ログ](observations/calculation-20261007T010837369691Z/report.json) と [全計算結果](observations/calculation-20261007T010837369691Z/result.json) に保存しました。実行は1子1回、実nice10、約0.307秒、終了コード0です。この時間は性能ベンチマークではありません。5秒の観測上限と別回収2秒を設定し、自動再試行はありません。

- [保存値の照合](observations/calculation-20261007T010837369691Z/verification.json)：6中心条件、12境界、24描画、48比較、入力拒否20件、変更検出16件が通過。模型を再実行していません。
- [標準出力](observations/calculation-20261007T010837369691Z/stdout.txt) と [標準エラー](observations/calculation-20261007T010837369691Z/stderr.txt)：計算結果と、同じ子で確認したnice値を分けて保持。
- [所有する子の回収確認](observations/calculation-20261007T010837369691Z/cleanup-readback.json)：子の終了と所有groupの不在を確認。共有ブラウザーや他プロセスは操作していません。
- [直前の資源読取り](observations/resources-20261007T010828333336Z.json)：完全なpsの文字列と解析行、CPU・メモリー、今回の識別条件を保存。過去の許可を流用していません。
- [画面への接続](observations/reader-connection.json) と [純粋な状態確認](observations/reader-state-check.json)：保存値・実行識別・日時・hashを固定。画面期待値は保存値の複製で、独立の数学的根拠は実装前の手表と別の区間照合です。



数値の意味は「独自の丸め規約とstrict LESSを組み合わせたら何が残るか」です。GPU・実API・実機・外部送信は0で、装置の丸めやちらつきを測定した結果ではありません。実画面の確認範囲は [GUI-QA](GUI-QA.md) へ分けます。
