# 一次資料と独自baseline模型

2026-10-06 JST公式Web確認。本文転載なし。

- [NASA SWE-052 Ver D](https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695427/SWE-052+-+Bidirectional+Traceability) §3.4 Software Design / §3.5 Software Test Procedures、§2 Rationaleの変更影響とconfiguration records。要求・設計・検証の関係と変更影響の入口。この6ID、digest構成、失効優先順位は原典の規範でなく独自模型。
- [NASA Appendix D Requirements Verification Matrix](https://www.nasa.gov/reference/appendix-d-requirements-verification-matrix/) 冒頭のmatrix説明。要求と検証方法の対応。本模型は実verificationを実行せずstored evidence適用を比較する。
- [NASA Appendix E Validation Plan](https://www.nasa.gov/reference/appendix-e-creating-the-validation-plan-with-a-validation-requirements-matrix/) 冒頭の計画入力/成果物。metadata一致を利用目的validation・人の変更承認に変換しない。

対応表が欠けた状態と有限canonical4関係の充足を区別する。製品全link完備・NASA適合・要求の正しさは未確認。ハッシュは合成内容の識別と記録変更検出のみ、署名ではない。
