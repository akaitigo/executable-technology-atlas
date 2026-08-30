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

署名検証済みReleaseの公開詳細はRelease payload digestを使うURLと、公開Projection JSONそのもののbytes digestを別々にIndexへ保持する。Browserは取得bytesをIndex digestへ再照合し、HTTP失敗、改変、不正JSONではTargetやEvidence詳細を採用せず、Indexに固定したRelease状態、Coverage分母、Definitive不足をlast-known-goodとして残す。

署名済みSubject Releaseがまだない場合、Portalは明示したclean commitのGit objectだけを開発時にCoreで監査し、観測専用のfixture署名Envelopeとして索引できる。この経路は`fixed-commit-incomplete`専用で、公開Release Trust、Release Manifest、Definitive Certificateを代替せず、Core Gateごとのpass/fail、Authority分母、必須output欠落、Schema drift、既知Gapを独立して保持する。現在は7 Subjectをこの境界で表示する。

固定commit監査の公開詳細は、attestation digestを使うcontent-addressed URLに加えて、生成Indexへ詳細JSONのbytes digestを保持する。Browserは両者を分離して検証し、取得bytes不一致や不正JSONでは詳細を採用せず、Indexの`fixed-commit-incomplete / Release未成立`とGap分母をlast-known-goodとして表示する。

RegistryはEnvelope読込前にpreflightし、singleton入力の重複、Release identity/digestの重複、異なるEntryによる同一Fileの再binding、Catalog外Subject/Repository、親Directory参照・絶対Path・fixture root外Path、全Path componentのsymlink、通常File以外、`stale`または`revoked`のlockを拒否する。`lockStatus`を持たない既存v1 Entryは互換上`current`として扱うが、未知状態も拒否する。preflight失敗はIndexとBootstrapを更新せず、診断だけをatomicなImport Reportへ記録する。

`frontend-behavior`のDepth Referenceは、明示Commit `4a0b2df8e2091a963bd0e0e1bbccef9c84b49a45`の`FE_DEPTH_REFERENCE.json`をSource digestと署名付きEnvelopeへ固定する。Importerは`contracts/depth-reference-lock.json`に対して18軸、状態、分母、Proof、Gapを検証し、生成IndexとDigest固定Subject詳細へ投影する。実行時にSubject checkoutは読まない。

Authority Human Reviewは明示Commitの`review-export.v1.json`、export Schema、packet Schema、packet index、80 packetをgzip固定Bundleと署名Manifestとして取込む。初期表示にはSubject横断summaryとpacket indexだけを含め、選択packetを静的JSONから遅延読込する。PacketはURL、locator、offset、digest、未review projection、machine-only proposalだけを保持し、一次資料本文をPortalへ複製しない。Portalのwrite capabilityは常にfalseで、将来のDecision書込みはCore共通API/Schemaの責務とする。

BrowserはAuthority exportをSource lockのexport digest、選択packetをexport内packet digestへWeb Cryptoで再照合してからJSONとして表示する。HTTP失敗、不正JSON、digest不一致ではHuman review詳細を採用せず、署名検証済みIndexのpending・reviewed・decision分母をlast-known-goodとして維持する。

PortalはHuman Decisionの正本を所有しない。UIが端末へ出力する候補は、手動一次資料確認と必須provenanceを検証するための提出物であり、固定Subject ReleaseのDecision Ledgerへ採用されるまで`reviewed`へ算入しない。`include | exclude | merge | split`がsemantic decisionで、`defer`はpendingを維持するworkflow holdとして分離する。

Evidence Dependency Graph Adapterは`reference-atlas-core`正式main/CI成功commit `072d7ca77981f51754e824d70c6d4ecd55ea67e5`のSchemaと`atlas audit . --gate evidence-dependency`結果へ固定する。Importerは署名済みsidecarのGraph digest、Core commit、Gate runtime identityを検証し、Graph自体とGate結果を分離して投影する。Portalはinput、transitive impacted output、rerun、required output、Proof/Closure構造をread-only表示し、GraphもSubject状態も書き換えない。固定ReleaseにGraphがない場合は97 Subjectすべてを個別に`missing-required-output`として残し、空集計や成功へ変換しない。

Portal自身のEvidence Dependency Graphは別の証跡である。`contracts/portal-evidence-dependency-inputs.json`がPortal Source、Harness、Runtime、Profileの分母を固定し、`npm run dependency:reproduce`が生成Index、非後退、Router Eval、SBOM、Build、Performance、Evidence、Provenanceを再実行してrun時刻とruntime identityを記録する。Graph checkに加え、隔離コピーでSource Digestとbindingだけを更新した負例を正式Core Gateへ渡す。このClosureはPortalのbounded証明だけを支え、SubjectのGap、Human review、`subject-definitive`欠落を変更しない。

Portal rootのDefinitive状態は`contracts/portal-root-definitive-lock.json`と`evidence/portal-root-definitive-report.json`で別に固定する。正式Core v2 CLIを実行して期待された失敗診断と6個のroot artifact欠落を再検証し、`root-definitive-incomplete`、配布`not-established`、completion effect `none`として扱う。Portal自身の実分母は`contracts/portal-root-surface-inventory.json`へ分離し、Mastery 14 SurfaceとCoverage 14 Targetを正本順で保持する。v1契約にSurfaceとTargetの個別edgeがないため対応を推測せず、Subject用`surface.inventory.yaml`も生成しない。空のartifactを置くこと、bounded v1 CertificateをDefinitiveまたは配布Closureへ読み替えること、digest更新だけで成功へ変えることを拒否する。

現時点で組込Indexが検証できる署名済み公開Releaseは0件である。7件のSubject bundleはtest-only鍵で署名した再現可能fixture候補であり、UI・Indexとも`fixture-only`として完成証明と分離する。

Core v1 Completion Certificateは固定Epochの`bounded-historical`として分類する。Releaseのraw `complete`、v1 Certificate検証、`public-release` Trustだけでは`subject-definitive`へ昇格しない。ReleaseはRepositoryごとの履歴配列とDigest固定の詳細Fileで保持し、current pointerをIndexで明示する。

Core Definitive Gate v2のSchema、Migration、CLIは正式main `072d7ca77981f51754e824d70c6d4ecd55ea67e5`で確定している。Portalは3 Schemaのbyte digestとGate commandを固定し、`completionPolicy.definitiveGate`を`core-v2-final-fail-closed`として扱う。署名済みbundle、公開Trust、固定Release binding、Core Gate passが揃わないSubjectは`subject-definitive-input-missing`または`subject-definitive-incomplete`のままにする。受理条件は[DEFINITIVE_GATE_V2.md](DEFINITIVE_GATE_V2.md)で管理する。

非後退BaselineはSubject、Target、Evidence、FailureをID単位で保持し、生成Indexとは独立した固定契約として扱う。Importer後に`scripts/check-non-regression.mjs`が現行Read ModelとDigest固定詳細を照合し、Publication Gateが結果の再現一致まで検証する。置換は明示Mappingが必要で、件数集約だけでは元のID、理由、環境、Evidenceを代替できない。

Depth Referenceの非後退契約は18軸の個別IDと全フィールドを固定入力へ照合する。Test数・Assertion数等の観測密度はProofとして保持するが、軸のpartialやGapを打ち消さず、`bounded=false`かつ`definitive=false`をfail closedで維持する。

公開表示Projectionは署名済み入力を信頼判定の正本として保持しつつ、画面・公開詳細・Portal文書へ自己宣伝や人物評価を複製しない。変換の有無とsource Release Digestを固定詳細へ記録し、Portalが表示する判断材料をCoverage、Evidence、制約、比較条件、実行結果に限定する。
