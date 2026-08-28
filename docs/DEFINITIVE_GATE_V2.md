# Definitive Gate v2 取込境界

この文書は実装済みのv2契約ではなく、Core正本確定までPortalが誤って完成表示しないための移行境界である。

## 現在の判定

- Schema Version 1の検証済みCompletion Certificateは`bounded-historical`とする。
- raw Manifestの`complete`は固定Epoch状態として表示し、`subject-definitive`とは表示しない。
- 未知のCertificate Schemaは受理せず、取込全体を隔離してlast-known-good Indexを維持する。
- 新規Subjectを自動昇格しない。
- Certificate履歴はRelease Digestごとの固定詳細として保持し、current Releaseとは別に索引する。
- 非後退BaselineよりSubject、Target、Evidence、Failureの粒度や可視性を下げない。`open required`と`unclassified`は未完了として明示する。

## Core確定後の受入条件

次のすべてをCore v2の確定Schema、Migration、CLIで検証できる場合に限り`subject-definitive`を返す。

1. 公開Trust Keyによる署名と失効・取消状態
2. Core v2 Definitive Certificateと固定Release Digestの一致
3. Authority-derived inventoryの全件Closure
4. Gap、`excluded`、`infeasible`の明示分類とfreshness
5. 実行Evidenceに束縛されたRuntime Profile / Runtime Identity
6. Core Definitive GateとMigration互換検証の成功
7. 非後退Baselineの成功と、旧ID Mappingを含む同等以上の情報・Evidence

フィールド名、Enum、署名形式、freshness規則はPortal側で推測しない。`reference-atlas-core`のversion、commit、Schema digestをvendor provenanceへ固定し、拒否Testを追加してから本Adapterを実装する。

## main反映条件

Core v2 Schema/Migration/CLI/Testが正本で確定し、PortalのImporter、UI、Router、Eval、Publication Gate、Portal自身のCertificateを同一契約へ移行した後に限る。それまではこのfeature branchをmainへmergeしない。
