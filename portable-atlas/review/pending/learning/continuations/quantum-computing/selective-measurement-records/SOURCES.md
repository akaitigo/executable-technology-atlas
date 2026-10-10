# IBM原典と有限算術

2026-10-06 JSTにIBM公式HTML本文を取得してlocatorを確認した。

- [Single systems / Quantum information](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/single-systems/quantum-information)、Measuring quantum states:標準基底の確率と測定後stateの説明。
- [Inner products and projections](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/quantum-circuits/inner-products-and-projections)、Projective measurements:射影の和がidentity、各結果の確率、選ばれた結果に応じた正規化stateを説明。
- [Convex combinations of density matrices](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/convex-combinations)、Probabilistic selections of density matrices:確率pkで選ぶdensityのstateは重み付き和で表す。

今回のσk=PkρPk、pk=Trσk、pk>0時ρk=σk/pkは1qubit Z射影への有限density拡張として契約に明記する。原典の一般射影・density概念から、任意POVMや実測定器の実証を主張しない。確率0 branchは割らない。記録を忘れたdensityとconditional stateを区別し、weighted ensemble/直接diagonal map/H後の全行列を独立算術で照合する。

取得不能だった短いsingle-systems URLは入口にせず、既存LEARNING_PATH指定のquantum-information本文を使用。第三者notebookやcredentialは保存しない。既存Subjectは文書参照だけでruntime依存しない。PRNG/実機shot/実測定recordなし。
