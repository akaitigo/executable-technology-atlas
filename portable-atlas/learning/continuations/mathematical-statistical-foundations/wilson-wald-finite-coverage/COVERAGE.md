# 有限coverage・中央受入待ち

今回の増分は、旧Waldのn8にWilson score intervalを追加し、9観測kの2図/包含と3既知pの256列加重coverageを比較すること。実装前手表・有理端点・反射対称性、独立score平方不等式/Fraction列重み、端点近似残差、固定区間と反復手続きの区別を教材化します。

n8/p文字列.1/.5/.9/z文字列1.96/k0..8以外は拒否。bounded Wilsonでもnominal95%保証なし。端点近似とexact有限massを分けます。旧rawは再計算・改稿しません。全分野・全Atlasの完了ではありません。

次3案は未実行で自動開始しません。
1. NIST exact binomial intervalを有限root bracketとFraction massで検算し、exactという語とsolver精度/保守性を分ける。
2. 独立性を外した明示joint分布で、Bernoulli積を流用したcoverageの誤りを比較する。
3. 別n/p/zを明示した契約で離散coverageの変化を比較し、今回の3pから一般優劣へ飛躍しない。
