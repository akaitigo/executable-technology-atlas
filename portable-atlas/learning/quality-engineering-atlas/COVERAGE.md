# QE Atlasの学習範囲と残る問い

章数を品質網羅率に換算しない。新規実装・実行済みは②の有限教材と関連するoracle/mutant検査だけ。既存教材の相対リンクは再利用入口で、各章の包括的実装を意味しない。

| 章 | 学習する問い・現在使える入口 | 今回の状態・未教材 | 次の小実験と根拠 |
|---|---|---|---|
| ① 品質要求/特性 | 利用者・目的・測定条件を要求IDへ落とす。[Requirements](../subjects/requirements-engineering/README.md) | 既存3要求matrixへのリンク。品質特性のtradeoff、elicitation、security/accessibility、安全、利用者validationは未教材 | 架空needs「速く受信/正しい結果」の衝突と受入条件。既存Requirements原典NASA Appendix C/Eの入口 |
| ② 測定/利用者結果 | server200とclient期限、全要求分母、受信だけのstatus、窓・打切り、平均/p50/p95 | 新規12決定的模型+実HTTP2attempt各2件。実利用者データ・欠測補正・測定誤差・分散clock・母集団推定は未教材 | collector欠落とlate arrivalの偏り。[Google SRE](https://sre.google/sre-book/service-level-objectives/) Indicators/Collecting/Aggregation |
| ③ テスト設計/リスク/coverage/mutation | 境界・反例・何を見逃すか。[SoftwareQuality](../subjects/software-quality-engineering/README.md) | 既存行coverage/境界mutationへのリンク。今回6 metric/raw mutantは検出検査のみ。riskモデル、統合/E2E、property、fuzz、test flakinessは未教材 | 要求の失敗影響と境界テストの優先順位。既存qualityのscopeとStryker metric原典へ |
| ④ 統計/SQC/実験計画 | 標本/母集団、条件/分母、測定系、ばらつき。[Math](../subjects/mathematical-statistical-foundations/README.md) | 既存有限Bayesへのリンクと分位点定義。管理図、工程能力、MSA、信頼区間、検定、多重比較、因果/無作為化/反復/交互作用は未教材 | 合成工程の管理図と変化検出、その後反復2因子実験。[NIST Process Monitoring](https://www.itl.nist.gov/div898/handbook/pmc/pmc.htm)、[Choosing a Design](https://www.itl.nist.gov/div898/handbook/pri/section3/pri3.htm) |
| ⑤ 信頼性/SLO | good/eligible/窓/目標とbudget。[SRE](../subjects/sre-incident-operations/README.md) | 既存有限budgetへのリンク。長期availability、寿命分布、冗長化、復旧、multiwindow alert、実on-callは未教材 | 期限と正しさのgood eventを固定し、collector欠落で予算がどう変わるか。[Google SRE SLO](https://sre.google/sre-book/service-level-objectives/) |
| ⑥ 改善/予防 | 観測と原因仮説、修正・確認・再発防止の有効性 | 今回timeout型分類を旧原票保持で修正/再観測。組織的postmortem、CAPA、変更効果/費用、toil削減、監査は未教材 | 架空incidentの根拠→action→再試験を残す。[Google SRE Postmortem](https://sre.google/sre-book/postmortem-culture/) |
| 別章 Taguchi/ロバスト設計 | 設計因子とnoise因子、平均とばらつき、parameter/tolerance design | 説明と一次資料入口だけ。SN比、損失関数、直交配列、aliasing/交互作用、確認実験、実測noise耐性は未教材。HTTP模型はTaguchi実験ではない | 小さい制御×noiseの全因子例を反復し、平均/分散tradeoffと確認runを検査。[NIST Taguchi](https://www.itl.nist.gov/div898/handbook/pri/section5/pri56.htm) |

まず利用者の目的→測定契約→有限反例→統計の前提→運用目標→改善の確認という往復を学ぶ。未知・pending・打切り・未実施を成功率100%へ隠さない。品質目標や規制適合、人の承認はこのAtlasから自動決定しない。
