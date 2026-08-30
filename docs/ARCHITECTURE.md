# Architecture

このPortalは97 Subject AtlasのRead Modelであり、個別技術の説明やSubject実装を所有しない。

```text
signed Catalog release + signed Subject release bundles
  -> Ed25519 / SHA-256
  -> Core JSON Schema + cross-manifest audit
  -> quarantine or verified candidate
  -> atomic generated Index
  -> Japanese search / detail / Router Skill
```

Runtimeは`fixtures/`のcontent-addressed bundleと生成済み`app/data/index.generated.json`だけを読み、Subject Source Tree、Git submodule、Default Branchへ依存しない。`scripts/generate-fixtures.mjs`はfixture更新時に明示された固定checkoutを入力として受ける開発用Exportであり、Runtime取込経路ではない。

`frontend-behavior`のDepth Referenceは、明示Commit `4a0b2df8e2091a963bd0e0e1bbccef9c84b49a45`の`FE_DEPTH_REFERENCE.json`をSource digestと署名付きEnvelopeへ固定する。Importerは`contracts/depth-reference-lock.json`に対して18軸、状態、分母、Proof、Gapを検証し、生成IndexとDigest固定Subject詳細へ投影する。実行時にSubject checkoutは読まない。

Authority Human Reviewは明示Commitの`review-export.v1.json`、export Schema、packet Schema、packet index、80 packetをgzip固定Bundleと署名Manifestとして取込む。初期表示にはSubject横断summaryとpacket indexだけを含め、選択packetを静的JSONから遅延読込する。PacketはURL、locator、offset、digest、未review projection、machine-only proposalだけを保持し、一次資料本文をPortalへ複製しない。Portalのwrite capabilityは常にfalseで、将来のDecision書込みはCore共通API/Schemaの責務とする。

PortalはHuman Decisionの正本を所有しない。UIが端末へ出力する候補は、手動一次資料確認と必須provenanceを検証するための提出物であり、固定Subject ReleaseのDecision Ledgerへ採用されるまで`reviewed`へ算入しない。`include | exclude | merge | split`がsemantic decisionで、`defer`はpendingを維持するworkflow holdとして分離する。

Evidence Dependency Graph Adapterは`reference-atlas-core`正式main/CI成功commit `072d7ca77981f51754e824d70c6d4ecd55ea67e5`のSchemaと`atlas audit . --gate evidence-dependency`結果へ固定する。Importerは署名済みsidecarのGraph digest、Core commit、Gate runtime identityを検証し、Graph自体とGate結果を分離して投影する。Portalはinput、transitive impacted output、rerun、required output、Proof/Closure構造をread-only表示し、GraphもSubject状態も書き換えない。固定ReleaseにGraphがない場合は97 Subjectすべてを個別に`missing-required-output`として残し、空集計や成功へ変換しない。

現時点で組込Indexが検証できる署名済み公開Releaseは0件である。7件のSubject bundleはtest-only鍵で署名した再現可能fixture候補であり、UI・Indexとも`fixture-only`として完成証明と分離する。

Core v1 Completion Certificateは固定Epochの`bounded-historical`として分類する。Releaseのraw `complete`、v1 Certificate検証、`public-release` Trustだけでは`subject-definitive`へ昇格しない。ReleaseはRepositoryごとの履歴配列とDigest固定の詳細Fileで保持し、current pointerをIndexで明示する。

Core Definitive Gate v2のSchema、Migration、CLIは正式main `072d7ca77981f51754e824d70c6d4ecd55ea67e5`で確定している。Portalは3 Schemaのbyte digestとGate commandを固定し、`completionPolicy.definitiveGate`を`core-v2-final-fail-closed`として扱う。署名済みbundle、公開Trust、固定Release binding、Core Gate passが揃わないSubjectは`subject-definitive-input-missing`または`subject-definitive-incomplete`のままにする。受理条件は[DEFINITIVE_GATE_V2.md](DEFINITIVE_GATE_V2.md)で管理する。

非後退BaselineはSubject、Target、Evidence、FailureをID単位で保持し、生成Indexとは独立した固定契約として扱う。Importer後に`scripts/check-non-regression.mjs`が現行Read ModelとDigest固定詳細を照合し、Publication Gateが結果の再現一致まで検証する。置換は明示Mappingが必要で、件数集約だけでは元のID、理由、環境、Evidenceを代替できない。

Depth Referenceの非後退契約は18軸の個別IDと全フィールドを固定入力へ照合する。Test数・Assertion数等の観測密度はProofとして保持するが、軸のpartialやGapを打ち消さず、`bounded=false`かつ`definitive=false`をfail closedで維持する。

公開表示Projectionは署名済み入力を信頼判定の正本として保持しつつ、画面・公開詳細・Portal文書へ自己宣伝や人物評価を複製しない。変換の有無とsource Release Digestを固定詳細へ記録し、Portalが表示する判断材料をCoverage、Evidence、制約、比較条件、実行結果に限定する。
