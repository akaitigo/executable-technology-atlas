# 有限COVERAGE

実装範囲は合成ABCD・4正weight・単一記号binary Huffman・独自bit header・明示0..255記号数です。一様とdyadic分布の手表、短文/等費用/長文/分布違い/空、6拒否、末尾bitflipが別の有効8記号列へなる反例、全341文字列（長0..4）×両方式682往復と13receiver負例、prefix・往復・加重平均・13full tree oracleを対象にします。未実行を保存QAとして数えません。画面証拠と最終照合はqaのverification.jsonを参照してください。

| 未教材 | 次の問い |
|---|---|
| 未知/zero weight alphabet拡張 | alphabet伝達と退化木をどう設計するか |
| 相関source・block Huffman | 単一記号最適からblock最適へどう進むか |
| LZW / arithmetic / adaptive coding | model・辞書を伝える費用をどう計上するか |
| 標準file format・byte padding | framing・checksum・コンテナを含めて比較できるか |
| 本物のdatasetと速度 | 実装/CPU/入力を固定した性能測定が別途必要 |
| channel coding・capacity・物理channel | 無雑音復号の例から通信保証へ飛躍しない |
| bit破損・認証 | 本receiverは一部形式不整合を拒否するだけで誤り訂正/改ざん検出保証はない |

中央受入待ちの有限候補です。元path・旧原票・global manifest/registry/Coreを更新せず、global gateは実行していません。
