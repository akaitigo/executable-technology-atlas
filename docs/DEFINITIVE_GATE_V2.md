# Definitive Gate v2 取込境界

この文書はCore正式main `072d7ca77981f51754e824d70c6d4ecd55ea67e5`で確定したDefinitive v2契約をPortalへ取り込む境界である。Portalはread-only Adapterとして実装済みだが、現在の97 Subjectには署名済みv2 bundleがないため、Definitive完成は0件である。

## 現在の判定

- Schema Version 1の検証済みCompletion Certificateは`bounded-historical`とする。
- raw Manifestの`complete`は固定Epoch状態として表示し、`subject-definitive`とは表示しない。
- 未知のCertificate Schemaは受理せず、取込全体を隔離してlast-known-good Indexを維持する。
- 新規Subjectを自動昇格しない。
- Certificate履歴はRelease Digestごとの固定詳細として保持し、current Releaseとは別に索引する。
- 非後退BaselineよりSubject、Target、Evidence、Failureの粒度や可視性を下げない。`open required`と`unclassified`は未完了として明示する。
- FE Depth Referenceは18軸中1 satisfied / 17 partialの`incomplete`として扱う。299/299等のTest成功は該当Proofに限定し、軸のGap、bounded、subject-definitiveの判定を代替しない。
- Authority Human Review read-only exportのpacket、projection、machine proposal、pending、reviewed、stale holdを個別に保持する。自動proposal、0 decision、`defer`をHuman review closureへ算入せず、本文を複製しない。Core共通API/Schemaが確定するまで書込みを提供せず、将来もreason、reviewer、time、manual-primary-source、digest、mappingが欠けるDecisionを拒否する。
- Evidence Dependency Graphは正式main commit `072d7ca77981f51754e824d70c6d4ecd55ea67e5`で確定した独立契約として取込む。Graph、rerun、runtime identity、required output、Proof/Closure構造のCore Gate結果はDefinitive完成の十分条件ではなく、Graph/Gate欠落、stale、failは既存Gapとincompleteを維持する。
- 実Subjectの固定clean commit監査は、active working treeやDefault Branchに依存しない観測入力としてのみ扱う。署名済みRelease Manifest、公開Trust Key、v2 Certificateがないcommitは、Coreの一部Gateがpassしても`fixed-commit-incomplete / Release未成立`とし、Subject Definitive入力件数へ算入しない。観測Envelopeのfixture鍵は公開Release Trustではない。

## 受入条件

次のすべてをCore v2の確定Schema、Migration、CLIで検証できる場合に限り`subject-definitive`を返す。

1. 公開Trust Keyによる署名と失効・取消状態
2. Core v2 Definitive Certificateと固定Release Digestの一致
3. Authority-derived inventoryの全件Closure
4. Gap、`excluded`、`infeasible`の明示分類とfreshness
5. 実行Evidenceに束縛されたRuntime Profile / Runtime Identity
6. Core Definitive GateとMigration互換検証の成功
7. 非後退Baselineの成功と、旧ID Mappingを含む同等以上の情報・Evidence

フィールド名、Enum、署名形式、freshness規則はPortal側で推測しない。`reference-atlas-core`のcommit、3 Schema digest、Gate commandを`contracts/definitive-v2-lock.json`へ固定し、不一致、fixture Trust、Gap、未Closure、未検証Runtime identityを拒否する。

## main反映条件

PortalのImporter、UI、Router、Eval、Publication Gate、非後退Gate、Portal自身のCertificateが同一契約を検証し、全Gateが再現可能に成功したcheckpointに限る。Subject v2入力の欠落は隠さず、外部公開やmain反映は別の明示的な作業として扱う。
