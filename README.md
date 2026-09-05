# 実行可能技術アトラス

97 Subject Atlasの固定ReleaseからManifest、Mastery、Coverage、Evidence、Skill Package、Completion Certificateを検証・探索する日本語Read Modelです。個別技術の知識は複製しません。

## ローカル実行

```bash
npm ci
npm run import
npm run non-regression
npm test
npm run eval
npm run build
npm run perf
npm run dependency:graph:check
npm run dependency:negative
npm run gate
npm run dev
npm run start
```

開発時は`http://localhost:3000`、build後の確認は`http://127.0.0.1:4173`を開きます。`npm run start`はvinextのproduction既定値`0.0.0.0`を使わず、`--hostname 127.0.0.1`でloopbackだけへbindします。別shellで`npm run start:verify-loopback`を実行すると、LISTEN addressと所有PIDをJSONで検証します。listenerなし、`0.0.0.0`、`*`、`[::]`、別port、正しいlistenerと不正listenerの混在はいずれもexit 1です。既定fixtureは完全にオフラインで再現できます。

現在のfeature branchにおける軽量tranche、実行済みGate、未実行heavy Gate、残Gapは[Portal integration status](docs/INTEGRATION_STATUS.md)に記録します。

## CLI

```bash
node scripts/atlas-portal.mjs search ゼロトラスト
node scripts/atlas-portal.mjs import
node scripts/atlas-portal.mjs verify
node scripts/atlas-portal.mjs evidence-status
node scripts/atlas-portal.mjs evidence-status --require-ready
node scripts/atlas-portal.mjs integration-status
node scripts/atlas-portal.mjs import-lifecycle
node scripts/atlas-portal.mjs root-readiness-status
```

`evidence-status`は現行bytesからEvidence wrapper、Graph input/output、実行runtime identityをread-onlyに再計算し、blockedでも観測結果としてJSONを返します。`--require-ready`の場合だけ、実再実行によるcurrent proofがなければexit 1で拒否します。どちらもEvidence、Graph、Indexを書き換えず、Subject、Distribution、Portal rootの完成状態に効果を持ちません。

`integration-status`はroot Artifact Gap、root Verification Matrix readiness、97 Subject Distribution／Gap、動的Evidence freshnessの各正本を再検証し、5/6 root欠落・1 present、970 Matrix cell、589 open Gap、0/97配布、freshness blockerを一つのJSONへ投影します。この出力は保存されない観測値で、Core Subject artifact、Evidence、Certificate、完成状態を生成または変更しません。

`import-lifecycle`は生成Index、Import report、Failure fixture、Registry負例から97 Subjectの実取込状態をread-onlyに再照合し、verified 7、quarantined 0、absent 90、未完成Release 7、stale Human review hold 3、Definitive v2 input 0をJSONへ投影します。Failure fixture 11件とRegistry負例14件は検証Coverageとして分離し、実Release状態や進捗へ加算しません。

`root-readiness-status`は`portal-root-definitive-report.json`に固定した6 root artifact gapと各readiness artifactをsame-originで再観測し、`verification.matrix.yaml`の実在を1 presentとして保持しつつ、`definitive.yaml`、`surface.inventory.yaml`、`depth.parity.yaml`、`migrations/definitive-v2.yaml`、`evidence/definitive-certificate.json`の欠落 5/6 をJSONへ投影します。この出力は保存されない観測値で、PortalをSubject化せず、Core root artifactのpartial presentをcompleteに読み替えません。

組込Indexで検証できる署名済み公開Releaseは現時点で0件です。7件のfixture署名付き候補は完成証明ではなく、取込・検索・失敗Fallbackを再現するための固定入力です。既知のSubject v1 Certificateは、公開固定Releaseとして取込まれるまで件数へ加えず、取込後も固定Epochの`bounded-historical`履歴として保持します。

## 完成と信頼の境界

- Core v1 Completion Certificateは固定Epochの形式的Closureを証明する`bounded-historical`です。Manifestが`complete`でもSubject Definitive完成とは表示しません。
- Subject Definitive完成への自動昇格はありません。公開Trust Keyと、確定したCore v2 Definitive Certificateを検証できるまで必ず未証明として扱います。
- `planned`、`active`、`incomplete`、Releaseなし、隔離を同じ完成状態に丸めません。Coverageの`excluded`、`infeasible`、`expired`も既定で表示します。
- Portal Repositoryは[GitHub PUBLICのmain](https://github.com/akaitigo/executable-technology-atlas)を正本とします。Portal自身のv1 `evidence/completion-certificate.json`もbounded証明であり、Subject Definitive完成数とは別軸です。
- Release詳細はDigest固定で保存し、同一SubjectのCertificate履歴を上書きしません。隔離が1件でもあれば生成Indexと詳細は更新せず、last-known-goodを維持します。
- CLIと検証Harnessは完全な`app/data/index.generated.json`を読み、Browser UIは小さな固定bootstrapから`public/data/index/<digest>.json`を同一originで取得します。両Indexのbytes、自己Digest、97 Subject、未完了集約をGateで照合し、取得またはbinding検証に失敗した場合は空Dashboardや完成0件を表示せず、`not-evaluated`のFallbackと直前に固定したGap集約だけを表示します。過去に公開したcontent-addressed IndexはImporterが削除しません。
- `contracts/non-regression-baseline.json`は97 Subject、246 Target、45 Evidence、11 Failure scenarioをID単位で凍結します。削除、未証明のStatus格上げ、boundedのDefinitive表示、Failure不可視化、Evidence切捨て、集約による粒度低下をGateで拒否します。
- 正当なID置換は`contracts/non-regression-mappings.json`に旧ID→新ID、理由、情報保持、同等以上のEvidence方針を明示する必要があります。旧固定Release自体は履歴から削除できません。
- UI、Portal Manifest、Docs、Routerは中立な事実、Coverage、Evidence、制約、比較条件、実行結果だけを記述します。自己宣伝、人物評価、推薦を目的化する文言をGateで拒否し、作者namespaceはRepository URLなど技術的に必要な識別に限定します。
- Core Definitive Gate v2のSchema、Migration、CLIは`reference-atlas-core`正式main/CI成功commit `072d7ca77981f51754e824d70c6d4ecd55ea67e5`で確定しています。Portalは3 Schemaと[24段階のMigration正本](contracts/reference/MIGRATION_DEFINITIVE_V2.md)をbyte digestで固定し、Authority-derived inventory closure、Gap、除外・実行困難、実Runtime Profile、Migration、Gate結果を[取込境界](docs/DEFINITIVE_GATE_V2.md)に従ってread-only表示します。現在は97 Subjectすべての署名済みv2入力が未収集のため、全件を`subject-definitive-input-missing`として表示します。
- Portal root自身へのCore v2 Definitive実監査も成功扱いにしていません。[固定監査report](evidence/portal-root-definitive-report.json)は6 artifact中5件欠落、`verification.matrix.yaml`のみpresent、`root-definitive-incomplete`、配布状態`not-established`を記録します。Portal固有の[Surface/Target実分母](contracts/portal-root-surface-inventory.json)は`mastery.yaml`の14 Surfaceと`coverage.yaml`の14 Targetを個別に固定し、v1正本にない対応edgeを推測しません。これはSubject用`surface.inventory.yaml`の代替ではなく、同artifactは欠落のままです。Coreが最初に報告する欠落artifactの順序には依存せず、既知分母内の読込失敗だけを受理します。既存v1 CertificateはboundedなローカルEvidenceとして保持されますが、Subject完成、配布Gap解消、Portal root Definitiveのいずれにも効果を持ちません。
- [Portal root Artifact Gap Index](evidence/portal-root-artifact-gap-index.json)は6欠落をCore正式mainの各Schema・Validator bytesへ固定します。Schema参照の存在をartifact存在と扱わず、欠落6、present 0、closed 0、`portalIsSubject=false`を維持します。
- [Distribution readiness](evidence/portal-distribution-readiness.json)は生成Indexの97 Subjectを個別に再照合し、固定Release、公開Trust、Authority inventory、Evidence Dependency、Core Definitive Gate、v2 Certificateのblockerを省略せず保持します。現在はready 0、Release表示7、公開Trust 0、Definitive v2入力0、Certificate 0で`not-established`です。件数、fixture Release、固定commit audit、Portal bounded Certificateを配布成立へ読み替えません。
- [Distribution input bindings](evidence/portal-distribution-input-bindings.json)は同じ97 Subjectについて、実在する固定Release 7件とattested clean commit監査7件をcontent-addressed公開artifactへ結びます。Release未結合90件、公開Trust結合0件、Definitive v2結合0件を明示し、Default Branch、active Subject tree、推測したDefinitive入力には依存しません。
- [Distribution Gap Index](evidence/portal-distribution-gap-index.json)はreadinessの8 blocker種・589 open instanceをSubject単位で保持します。削除、集約置換、別Subjectへの付替え、source locator移動、Closure Evidenceなしのclose、件数だけによる配布成立を拒否し、closedは0のままです。
- [Portal配布検証Matrix](evidence/portal-distribution-verification-matrix.json)はImporterが97 Subjectへ投影したnormal/boundary/refusal/failure/recovery/migration/operations/security/performance/compatibilityの10 class、計970 cellを固定します。現在は個別条件verified 201、gap 478、実Runtimeなしで`not-evaluated` 291です。これはPortal infrastructure artifactであり、欠落中のCore Subject用`verification.matrix.yaml`を満たしません。
- [Import lifecycle visibility](evidence/portal-import-lifecycle-visibility.json)は実取込のverified 7、quarantined 0、absent 90、未完成Release 7、履歴失効 0、stale Human review hold 3を97 Subjectの個別状態へ固定します。Failure fixture 11件とRegistry負例14件は検証Coverageであり、実Release、進捗、完成件数へ数えません。stale/revoked lockはpreflightで拒否し、last-known-good Indexを保持します。
- [Portal root Depth parity readiness](evidence/portal-root-depth-parity-readiness.json)は欠落中のCore Subject用`depth.parity.yaml`を生成せず、Core固定Schema/Validator、Portal固有14 Surface/14 Target、97×10配布Matrix、記録済みGraphのrequired output bindingを再照合します。6 prerequisiteは全件blocked、Core artifact present 0、completion effect noneです。Portal固有Surface、配布Matrix、Graph内の`status=current`をSubject Depth parityや実rerun proofへ代用しません。
- [Portal root Migration readiness](evidence/portal-root-migration-readiness.json)は欠落中の`migrations/definitive-v2.yaml`を生成せず、Core Migration正本、既存v1 Certificate payload、root/Depth/Distribution/Graph状態を固定します。v1 payload Digest検証だけをsatisfied 1とし、履歴copy、Portal Subject migration Authority、root前提artifact、actual Graph rerunをblocked 8として保持します。v1 Certificateと24 actionのReference文書はDefinitiveまたはMigration artifactではありません。
- [Portal root Definitive Certificate readiness](evidence/portal-root-definitive-certificate-readiness.json)は欠落中の`evidence/definitive-certificate.json`を発行しません。root artifact、公開Trust、固定Definitive v2入力、Core Gate pass、Depth、Migration、current Graph rerunの10 prerequisiteを全件blockedとして保持し、既存bounded v1 Certificateのpayload整合性をDefinitive完成へ読み替えません。Definitive Certificate 0、auto issue false、completion effect noneです。
- [Portal root Definitive declaration readiness](evidence/portal-root-definitive-declaration-readiness.json)は欠落中の`definitive.yaml`を生成しません。Portal非Subject境界、Core Surface/Matrix/Depth/Migration/Certificate、公開Trust・Core Gate、current Graph rerunの9 prerequisiteを全件blockedとして保持します。Portal固有adapterをCore Subject artifactへ代用せず、Declaration 0、auto create false、completion effect noneです。
- [Portal root Surface Inventory readiness](evidence/portal-root-surface-inventory-readiness.json)はCore契約固定とPortal v1の14 Surface / 14 Target分母保持だけをsatisfied 2とし、Portal Subject Authority、Authority-derived denominator、明示mapping、Core artifact、Definitive binding、current Graph rerunをblocked 6として保持します。個別edgeを推測せず、`surface.inventory.yaml`は欠落のままです。
- [Portal root Verification Matrix readiness](evidence/portal-root-verification-matrix-readiness.json)はCore契約固定、97 Subject × 10 classのPortal配布分母保持、実在する`verification.matrix.yaml`のSchema/validator整合だけをsatisfied 3とし、Portal Subject Authority、Authority-derived atomic behavior、Core Surface Inventory、291 not-evaluated runtime cell、current Graph rerunをblocked 5として保持します。artifact present は completion effect を持ちません。
- [Portal CI checkpoint readiness](evidence/portal-ci-checkpoint-readiness.json)は97 Subject集約、Root/Distribution/Graph、署名方針、Workflowの対象SHAを一つのread-only契約へ固定します。exact head checkout・最小権限・SSH/DCO方針だけをsatisfied 3とし、Subject Definitive 0/97、Distribution ready 0、root artifact missing 5、dirty tree、Graph stale、push/PR同一SHA CI未成立をblocked 6として保持します。記録HEAD/upstreamはpre-checkpoint baseであり、現HEADの祖先かつ同一であることを検証しますが、それだけではcandidate commitやcheckpointとしません。
- `frontend-behavior`は`frontend-behavior-atlas` commit `4a0b2df8…`の`FE_DEPTH_REFERENCE.json`を固定取込します。18軸中1 satisfied / 17 partial、status `incomplete`を軸別の分母・Proof・Gapとともに表示し、299 E2E Test等の成功をboundedまたはDefinitive完成へ読み替えません。
- Authority Human ReviewはFE commit `6c2cfa41…`の固定read-only exportと2 Schemaを正本入力にします。80 packet/deep-link、230 candidate projection、113 machine proposal、3 stale relock hold、human decision 0件をDigest検証し、機械proposalをHuman decisionとして表示しません。
- Portalは一次資料本文を複製せず、URL、locator、offset、digestを表示します。Decision候補も保存・送信しません。将来の書込みはCore共通API/Schemaへ分離し、reviewer、time、reason、`manual-primary-source`、source/tool/context digest、旧→新mappingが揃わない操作を拒否します。`defer`と選択前stale relockはpendingのread-only holdです。
- Evidence Dependency Graphは`reference-atlas-core`正式main/CI成功commit `072d7ca77981f51754e824d70c6d4ecd55ea67e5`のSchemaとGate契約へ固定します。各Subjectのinput changed/current、影響output、stale/current、rerun command/result/runtime identity、missing required output、Proof/Closure structure driftをread-only表示します。GraphまたはCore Gate結果がない現在のSubjectは`missing-required-output`のままで、digest更新だけを復旧や完成へ読み替えません。
- Portal自身は`evidence/dependency-graph.json`で4入力群と全派生Evidenceを固定し、`npm run dependency:reproduce`で実再実行を記録します。`npm run dependency:negative`はSource Digestとbindingだけを更新した隔離コピーがCore Gateで失敗することを検証します。このPortal bounded Closureは97 Subjectの`subject-definitive`を1件も補いません。
- [Evidence refresh policy](contracts/portal-evidence-refresh-policy.json)は8 Evidence wrapper、4 Graph入力、全discovered output、Import／Non-regression／Eval／SBOM／Build／Performance／Evidence／Provenanceの8段階を動的に再照合します。現在はstale wrapper 3、前回run後変更input 3、未記録output 14のためblockedです。wrapper Digestの書換え、stage skip、Mock runtime、Graphの記録済み`status=current`を実再実行へ代用しません。
- ImporterはRegistryを登録Envelope読込前に検証し、singleton SubjectまたはRelease identityの重複、異なるEntryによる同一Fileの再binding、Catalog外binding、親Directory参照・絶対Path・fixture root外Path、全Path componentのsymlink、通常File以外、`stale`または`revoked`のlockを拒否します。失敗時は検証済みIndexとBootstrapを更新せず、last-known-goodを維持します。
- `argocd`は`argocd-reference-atlas`のclean commit `37db7c88…`をGit objectからread-only監査した観測Envelopeを表示します。Core通常AuditとEvidence Dependency Gateはpassですが、署名済みRelease Manifest、公開Trust、v2 Certificate、Depth parityがなく、open required 22件、Authority未分類63,889件、Scenario Proof Schema driftが残るため`fixed-commit-incomplete / Release未成立`です。この入力も97 SubjectのDefinitive入力欠落を補いません。
- `postgresql`は`postgresql-reference-atlas`の署名済みclean commit `727aef05…`を同じ境界で監査します。Core通常Audit、Evidence Dependency（12 input、9 changed、443 output）、Non-regression、Scenario Trace、Evidence durability Gateはpassしていますが、署名済みRelease Manifest、公開Trust、v2 Certificateがなく、open required 27件、Authority未分類5,512件、Human decision 0件、Scenarioは290行中16行だけが専用runtime proofを持ち274 gap、Authority atomic binding 0、completion eligible 0のため、Definitive Gateはrequired Targetの`partial`でfailします。
- `flutter`は`flutter-reference-atlas`のclean commit `45980f04…`を同じ境界で監査します。Core通常Auditはpassしますが、open required 2件、Evidence Dependency必須output欠落1件、Authority未分類74件・Human decision 0件・stale hold 3件、Scenario runtime gap 531件が残ります。Authority/ScenarioのCore v2 Schema drift、Definitive契約3 artifact、Non-regression契約、Evidence durability outputも欠けるため、各Gateのfailをそのまま表示しReleaseやDefinitiveへ昇格しません。
- `rabbitmq`は`rabbitmq-reference-atlas`のclean commit `a500e567…`を監査します。Core通常AuditとEvidence Dependency Gateはpassしますが、open required 203件、changed input 2件、Authority未分類・Human review待ち各1,579件、stale hold 2件、Scenario runtime gap 925件が残ります。`definitive.yaml`の`subject-definitive`自己宣言は、Verification matrix・Depth parity・v2 Certificate・公開TrustがなくCore Definitive Gateもfailするため、Portalでは`not-definitive`として表示します。
- `kotlin`は`kotlin-reference-atlas`のclean commit `39da6284…`を監査します。Core通常Audit、Evidence Dependency、Authority、Scenario、Non-regressionの各契約検証は実行できますが、open required 3件、Authority locator defer 18件、未分類・Human review待ち各146,402件、Scenario runtime gap 690件が残り、Evidence durabilityは未実行の`status=failed`です。`definitive.yaml`の`subject-definitive`自己宣言はCore Definitive Gateが`authority.locator-extraction=partial`を拒否するため、Portalでは`not-definitive`として表示します。
- `zero-trust`は`zero-trust-reference-atlas`の署名済みclean commit `0a355a78…`を監査します。10 Scenario matrixは910行を保持し専用Runtimeで28行・56/1,820 Variant cellを閉じましたが、882行・1,764 cell、Authority atomic binding 91件、18軸中17 partial、Human decision 0が残り、completion eligible rowは0です。Evidence Dependency GateとNon-regressionはpassしますが、`surface.inventory.yaml`、root `depth.parity.yaml`、v2 Certificate、Evidence durability outputがなくCore Definitive Gateはfailするため、Matrix検証成功や既存v1 Certificateを`subject-definitive`へ昇格しません。
- `frontend-behavior`はread-only exportの固定commit `6c2cfa41…`をGit objectから監査します。Core通常Auditはincompleteでopen required 85件、Authority anchor 15,963件は全件Human review待ち、exportは80 packet・230 projection・113 machine proposal・decision 0、Depthは1 satisfied / 17 partialです。Evidence Dependency Graph、Scenario Proof、Non-regression、Durability、Definitive契約入力がないため各Gateのfailを保持し、299 E2E Test等の件数を完成へ読み替えません。
- `npm run gate`はPortal契約、Evidence、SBOM、Release署名、DCO、証明対象Commitを検証します。Core正本の`atlas audit`と`atlas certificate verify`も完成条件です。

## Continuous Integration

`.github/workflows/publication.yml`は、全pushと`main`向けPull Requestをクリーンな`ubuntu-24.04` runnerで検証します。GitHub公式Actionはcommit SHA、Node.jsとGoは完全Version、Completion Certificate検証用Core v1は`cf9e6e2d…`、Evidence DependencyとDefinitive v2契約は正式main `072d7ca…`へ固定し、npm依存は`package-lock.json`だけから`npm ci --ignore-scripts`で導入します。

Workflowの権限は`contents: read`のみで、秘密情報、永続Credential、依存Cacheは使いません。固定Index、非後退結果、Router Evalの再現一致、全Test、Lint、Build、Portal GraphのDigest/構造、digest-only負例、Publication Gate、Core v1 Audit/Certificate、Core v2 Evidence Dependency Gateを通し、runner内で追跡対象ファイルが変わった場合は拒否します。

容量制約時は`node --test tests/registry.test.mjs tests/importer-registry.test.mjs tests/non-regression-registry.test.mjs tests/dependency-contract.test.mjs`でRegistryのbuilt-in検証だけを再実行できます。既存12境界にstale/revoked lockを加えた14負例を検証しますが、Ajvを含むlockfile依存導入後のfull Importer、Non-regression、Build、Publication、Core Gateを代替せず、対象unit成功だけではcheckpointまたは完成としません。

Repository admissionはengineering-control-plane commit `00fe010a…`からrolloutされた`repo.yaml`を正本とし、Portal自身のGitHub writeだけを許可します。cloud writeと他Repositoryへのwriteは拒否し、この境界をPublication GateとProvenanceで検証します。

Commit署名は`e4e3e48f…`を非破壊な施行境界とします。それ以前のDCO付きunsigned履歴をamend、rebase、force pushせず、以後のcheckpointはDCOとSSH/GPG署名の両方を要求します。`security/allowed_signers`には既存履歴の検証鍵と現在のGovernance鍵を併記し、各commitへ`git verify-commit`を実行してPublication Gateとclean-room CIで検証します。
