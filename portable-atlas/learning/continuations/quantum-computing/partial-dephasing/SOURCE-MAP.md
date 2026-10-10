# Atlas：部分的な位相緩和の根拠と既存経路

実在するファイル索引から次を読んだ。部分dephasingの探索は既存資料の有限範囲であり、PC全体の不存在を断定しない。



2026-10-06、公式IBM本文を正規webで読取。本文bytesは保存せず本文hashは主張しない。取得に失敗したURLは今回なし。

| 公式資料 | 実読した範囲 | この教材との対応 |
|---|---|---|
| [Density matrix basics](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/density-matrix-basics) | Definition、Positive semidefinite matrices、Interpretation | trace1、Hermitian/非負固有値、対角の測定確率と非対角を区別 |
| [Convex combinations](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/convex-combinations) | Probabilistic selections、完全混合状態 | 重み付き密度の和、ベクトル平均と区別、分解は唯一でない |
| [Channel representations](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/quantum-channels/representations-of-channels) | 完全dephasingの代替表現、行258–277、Unitary channels | D(ρ)=(ρ+ZρZ)/2、UρU†。ここから今回のE_pを整理するとq=p/2 |

pの3値、入力3状態、C_Z=|ρ01|という指標、pをqと誤読した有限対照は今回の教材規約。原典の一般channel理論を実装全体の保証として引用しない。元担当の現在状態は未確認、共有元/旧教材/台帳へ書込や統合は行わない。
