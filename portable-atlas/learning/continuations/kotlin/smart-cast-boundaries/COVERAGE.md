# Kotlin：smart cast境界の対応範囲

分野ゴールは <code>2026-10-06/task-8/atlas-97-field-goals-ja.md</code> の「23. Kotlin」、特に次課題の変更可能なproperty・独自getterです。前教材 <code>../kotlin-null-operators/COVERAGE.md</code> のsmart cast残課題に対応します。旧教材の実行・画像原票は再利用した観測として加算せず、変更もしません。

| 観点 | 今回保存したもの | 状態・残る範囲 |
|---|---|---|
| mutable property | null検査後に再読取りする拒否例、local valで受け取る対照 | 固定compilerでSMARTCAST_IMPOSSIBLE・JARなしを観測 |
| custom getter | 1回目だけ初期値を返すgetter、直接smart castの拒否例 | 固定compilerでSMARTCAST_IMPOSSIBLE・JARなしを観測 |
| stable local val snapshot | 元propertyの逐次変更後も保存値を使う経路 | Ada/nullの2条件を実行し、固定stdoutと一致 |
| getter snapshot対再読取り＋!! | getter呼出順とNPEの差を比較する対照 | 各Ada/null、計4条件を実行。正常3・意図したNPE1 |
| 拒否と実行時失敗の分類 | compile3条件：受理1/拒否2、runtime6条件：正常5/NPE1 | 全件を実測。拒否/NPEを正常終了へ加算しない |
| 再現と検証 | 低優先度・時間制限・全体資源ゲート付きrunner、保存原票の独立verifier | Kotlin 2.4.10/JDK17.0.17、固定source不変、独立49項目pass |
| 視覚的な案内 | 原票reader、模式図、正常/異常の比較表 | 作者GUI 24項目・91操作pass、1280/390実capture 7枚を目視。模式図と実行原票を区別 |
| readerの状態変化 | 予想変更・reset・取得失敗・digest不一致・遅延応答 | 本文/原票/答えの消去、旧success/errorによる新状態の上書き防止を実browserで確認 |
| 並行性と状態の一貫性 | 明示的な1thread内の逐次変更を使う設計 | lock・transaction・atomic性・大域concurrencyは実証しない |
| その他のsmart cast条件 | 原典への参照 | open/module/delegation/capture/contract等は今回対象外 |
| Atlasの受入・統合 | 別reviewerへの独立受入依頼 | 作者QAと独立受入を区別。統合・既存台帳・旧sourceは未変更 |

根拠は2026年10月6日の[実測と答え合わせ](observations/operational-revision-20261006T054006019240Z/README.md)、[原票](observations/operational-revision-20261006T054006019240Z/run.json)、[独立検証](observations/operational-revision-20261006T054006019240Z/verification.json)です。以前の保留原票は履歴として保持しています。

readerの根拠は[最終GUI原票](browser-qa/run-2026-10-06T060934919Z/report.json)と[作者画像目視](browser-qa/visual-review.json)です。GUI QAでKotlinを再実行していません。最終sourceとcaptureの対応は[binding](browser-qa/gui-revision-20261006T060214056778Z/final-binding.json)で確認できます。

「全propertyを理解・検証した」「この方法で並行安全になった」とは扱いません。説明、変更していない固定期待値、当Macでの有限ケースの実観測を区別します。
