# Portal integration status

更新日: 2026-08-31

この文書は現在のfeature branch上の未checkpoint差分を記録する。Release、Completion Certificate、Core Gate結果ではなく、Portal自身またはSubjectの完成効果を持たない。

## 今回の軽量tranche

- 97 Subjectそれぞれについてcurrent import、current Release status、trust usage、履歴statusを`evidence/portal-import-lifecycle-visibility.json`へ固定した。
- 実取込のverified 7、quarantined 0、absent 90、未完成Release 7、公開Trust 0、履歴失効 0、stale Human review hold 3、Definitive v2 input 0をFailure/Registry fixtureから分離した。
- Failure fixture 11件、Registry負例14件、stale lock 1件、revoked lock 1件は検証Coverageとして保持し、実Release状態または進捗に加算しない。
- Lifecycle Schema、Verifier、7負例、root report binding、Publication Gate binding、日本語UI、Evidence Dependency Graph required-output discoveryを接続した。
- `atlas-portal import-lifecycle`、same-origin `/api/import-lifecycle`、browser guardを追加し、Import lifecycleを動的read-only観測としてUIへ接続した。fetch/shape failure時も`not-evaluated`で停止し、stale/revoked拒否やlast-known-goodを弱めない。
- Core Subject用`depth.parity.yaml`を作らず、Portal root Depth parity readinessの6 prerequisiteを全件blockedとしてCore契約、root report、日本語UI、Graph discoveryへ接続した。Portal adapter、記録済みGraph status、DigestだけのClosureを拒否する。
- Core Subject用`migrations/definitive-v2.yaml`を作らず、Portal root Migration readinessをsatisfied 1 / blocked 8として接続した。bounded v1 source、固定Reference、履歴copy、actual Migration artifact、Graph current proofを混同しない。
- Core Subject用`evidence/definitive-certificate.json`を発行せず、Portal root Definitive Certificate readinessをsatisfied 0 / blocked 10として接続した。bounded v1、公開Trust 0、Core Gate pass 0、記録済みGraphをDefinitive Certificateへ代用しない。
- Core Subject用`definitive.yaml`を生成せず、Portal root Definitive declaration readinessをsatisfied 0 / blocked 9として接続した。Portal adapter、配布Matrix、Certificate readinessをCore Subject declarationへ代用しない。
- Core Subject用`surface.inventory.yaml`を生成せず、固定Core契約とPortal v1の14 Surface / 14 Target分母保持をsatisfied 2、Authority-derived denominator、mapping、artifact、Definitive binding、current rerunをblocked 6として接続した。
- Core Subject用`verification.matrix.yaml`はPortal root artifactとして実在するが、固定Core契約と97 Subject × 10 class分母保持、Schema/validator整合だけをsatisfied 3とし、Authority-derived atomic behavior、Core Surface、実Runtime、current rerunをblocked 5として接続した。artifact present は completion effect を持たない。
- same-origin `/api/root-verification-matrix-readiness`、browser guard、UI境界を追加し、Portal root verification matrix readinessを専用の動的read-only観測として表示する。fetch/shape failure時も`not-evaluated`で停止し、97×10配布分母や`not-evaluated`をCore artifact presentへ読み替えない。
- Subject集約とCI raceを`portal-ci-checkpoint-readiness`へ接続した。exact head checkout、最小権限、署名/DCO方針をsatisfied 3、Subject Definitive、Distribution、Root、dirty tree、Graph、push/PR same-SHA CIをblocked 6として保持する。
- same-origin `/api/ci-checkpoint-readiness`、browser guard、UI境界を追加し、Portal CI checkpoint readinessを専用の動的read-only観測として表示する。fetch/shape failure時も`not-evaluated`で停止し、記録baseのHEAD一致やdirty treeをsame-SHA CI成功へ読み替えない。
- Portal配布検証Matrixは97×10=970 cell、verified condition 201、gap 478、実Runtimeなしのnot-evaluated 291を維持する。Core Subject用`verification.matrix.yaml`は欠落したままである。
- Evidence refresh policyをtracked Evidenceではなく動的read-only契約として追加した。8 wrapper、4 input、39 discovered output、8段階の既存`dependency:reproduce`を照合し、Graphを説明するreportをGraph outputへ追加する自己参照を避ける。現在はstale wrapper 3、前回run後変更input 3、未記録output 14でblockedである。
- `atlas-portal evidence-status`へ同じ動的判定をread-only接続した。通常はblockedをJSONで正直に返し、`--require-ready`はcurrent proofがないためexit 1となる。Graph/Evidenceのmtime不変、Subject/Distribution/root completion effect noneをtargeted testで検証する。
- same-origin `/api/evidence-status`、browser guard、UI境界を追加し、Portal Evidence refreshを専用の動的read-only観測として表示する。fetch/shape failure時も`not-evaluated`で停止し、recorded Graph statusだけをcurrent proofへ格上げしない。
- `portal-integration-status` Schemaと非永続CLI projectionを追加し、root artifact missing 6/6、Matrix 970 cell（478 gap / 291 not-evaluated）、Distribution ready 0/97・589 open Gap、Evidence refresh blockedを一回のread-only照合へ接続した。9負例は各分母の縮小、Gap隠蔽、Portal Subject化、自動実行、完成昇格を拒否する。
- `portal-root-readiness-status` Schemaと非永続CLI projectionを追加し、6 root artifactのうち5 missing / 1 presentを一回のread-only照合へ接続した。same-origin `/api/root-readiness-status` と browser guard はartifact順序、欠落 5/6・present 1/6、`portalIsSubject=false`、`completionEffect=none` を exact に検証し、fetch/shape failure時も`not-evaluated`で停止する。
- `portal-root-artifact-gap-index` は current state を 5/6 missing・1/6 present のまま保持しつつ、実filesystemに一致するpresent/missing/open/closed集計だけを許すよう一般化した。phantom present、summary偽装、digestだけのClosure、Portal Subject化は負例として拒否し、partial presentを完成扱いしない。

## 実行済みの軽量Gate

- Distribution readiness/binding/gap/matrix、Import lifecycle、既存root readinessを含む追加Node test: 35/35 pass
- Verification Matrix readiness、root report、Non-regression負例を含む今回のtargeted Node test: 24/24 pass
- CI checkpoint readiness、Root/Matrix binding、Non-regression負例を含む追加targeted Node test: 20/20 pass
- root verification matrix readiness API targeted Node test: 1/1 pass
- Distribution readiness/binding/gap/matrixとroot artifact gapの直接・負例targeted Node test: 10/10 pass
- Evidence refresh policy直接・9負例・read-only CLI targeted Node test: 3/3 pass
- Evidence refresh API targeted Node test: 1/1 pass
- CI checkpoint readiness API targeted Node test: 1/1 pass
- Portal integration status直接・9負例・read-only CLI targeted Node test: 3/3 pass
- Portal root readiness status直接・8負例・read-only CLI/API/browser boundary targeted Node test: 6/6 pass
- dynamic integration/root verification matrix/CI checkpoint/evidence refresh/import lifecycle/root readiness の same-origin + aria-live アクセシビリティ回帰 test: 17/17 pass（`tests/accessibility.test.mjs`内）
- Import lifecycle直接・7負例・read-only CLI/API/browser boundary targeted Node test: 4/4 pass
- CI checkpoint記録baseを`HEAD^`へ置換したclean-runner相当の祖先性検証: pass。現行入力Digestを維持したまま後続commitでも再現でき、candidate/same-SHA CIへは昇格しない。
- Non-regression: 97 Subject / 246 Target / 45 Evidence / violation 0
- ESLint: pass
- Core正式main `072d7ca77981f51754e824d70c6d4ecd55ea67e5`を使うPortal root check: expected failを検証しpass、root artifact missing 6、completion effect none
- 既定の隣接Core checkoutは`46db1eb0e68d00c09f34994dd66ad6d44d3f6ef1`へ進んでいるため固定SHA checkがfail-closedで拒否した。`/private/tmp/reference-atlas-core-072-git`の固定Git checkoutを明示したroot gap/root checkはともにpassした。既定branchへ追従して契約を変更していない。
- Lifecycle check: pass、actual verified 7 / quarantined 0 / absent 90 / incomplete 7 / expired 0
- Integration status check: pass、root missing 5/6 + present 1/6 / matrix gap 478 / not-evaluated 291 / distribution ready 0/97 / open gap 589 / refresh blocked
- Graph output discovery: lifecycle、Depth、Migration、Certificate、Definitive declaration、Surface Inventory、Verification Matrix、CI checkpoint readiness artifactに加えて、append-onlyな旧content-addressed Indexも保持した39 outputを列挙

## 未実行と残Gap

heavy runtime停止条件のため、Browser、Build、Performance、`npm run dependency:reproduce`、full testはこのtrancheで実行していない。これらを軽量Gateで代替しない。Verification Matrixの8負例、CI checkpoint readinessの9負例、Evidence refresh policyの9負例、Integration statusの9負例、Import lifecycleの7負例に加え、Distribution readiness、固定input binding、589 Gap、97×10 Matrix、root artifact 6 Gap、read-only CLI/API/browser boundaryを必須成果物として接続したPublication Gateの最新read-only実行は354/355で、失敗はPortal自身のEvidence Dependency Graph 1件だけである。`npm run definitive:root:record`、`import:lifecycle:record`、`distribution:*:record`、`checkpoint:readiness:record`、`npm run import`、`npm run non-regression`、`npm run evidence`を現在のdirty差分に対して再実行したため、record済み`evidence/dependency-graph.json`はfail-closedで次を報告する。

- input changed: `portal-source`、`portal-harness`、`portal-runtime`、`portal-profile`
- stale wrapper: 0 / 8
- missing required output: 14
- content-addressed current index未記録: `public/data/index/25c8ba3c8b0560f1a99f992e097c853d0a594849fda2ad445768ee060583332f.json`
- 新規readiness/import/distribution artifact未記録: `evidence/portal-ci-checkpoint-readiness.json`、`evidence/portal-distribution-gap-index.json`、`evidence/portal-distribution-input-bindings.json`、`evidence/portal-distribution-readiness.json`、`evidence/portal-distribution-verification-matrix.json`、`evidence/portal-import-lifecycle-visibility.json`、`evidence/portal-root-artifact-gap-index.json`、`evidence/portal-root-definitive-certificate-readiness.json`、`evidence/portal-root-definitive-declaration-readiness.json`、`evidence/portal-root-depth-parity-readiness.json`、`evidence/portal-root-migration-readiness.json`、`evidence/portal-root-surface-inventory-readiness.json`、`evidence/portal-root-verification-matrix-readiness.json`
- 旧content-addressed index rebinding拒否: `public/data/index/76090e9b725c469db2cfbe02a8c5f3ab8874b6422cba88d37bd7bec6e7aed3b0.json`

この1件はrecorded Graphの手編集やDigest更新だけでは閉じない。`contracts/portal-evidence-refresh-policy.json`と`contracts/portal-dependency-reproduce-order.json`が要求するとおり、heavy slot解放後に`npm run dependency:reproduce`でImport→Non-regression→Eval→SBOM→Build→Performance→Evidence→Provenanceを同一runで再実行し、その後に`npm run gate`を再実行する必要がある。軽量recordやbounded Portal証明をcurrent proofへ読み替えない。

既存Graphは前回の実runに基づくため、今回追加したDistribution/Lifecycle artifact、生成Index、root reportのdigestとrequired outputをまだ含まない。Graph checkはこの差分をstale/missingとしてfail-closedに報告する。Graph JSONを手編集せず、heavy slot解放後に既存entrypointでImport、Non-regression、Eval、SBOM、Build、Performance、Evidence、Provenanceを実再実行して更新する。

正本Gapは次のままである。

- Portal root Core v2 artifact: missing 5 / present 1 / closed 1
- Portal root Depth parity readiness: prerequisite satisfied 0 / blocked 6 / Core artifact present 0
- Portal root Migration readiness: prerequisite satisfied 1 / blocked 8 / Core artifact present 0
- Portal root Definitive Certificate readiness: prerequisite satisfied 0 / blocked 10 / Core artifact present 0 / auto issue false
- Portal root Definitive declaration readiness: prerequisite satisfied 0 / blocked 9 / Core artifact present 0 / auto create false
- Portal root Surface Inventory readiness: prerequisite satisfied 2 / blocked 6 / Core artifact present 0 / invented edge 0
- Portal root Verification Matrix readiness: prerequisite satisfied 2 / blocked 6 / Core artifact present 0 / not-evaluated 291
- Portal CI checkpoint readiness: prerequisite satisfied 3 / blocked 6 / checkpoint ready false / same-SHA CI false
- Subject Definitive v2 input: missing 97 / subject-definitive 0
- Distribution: ready 0 / 97、open blocker instance 589 / closed 0
- 公開Trust binding 0、Definitive Certificate binding 0、Evidence Dependency current 0
- Distribution Matrix: gap 478、not-evaluated 291
- Authority Human decision 0、stale hold 3

したがってPortal rootは`root-definitive-incomplete`、distributionは`not-established`、Goalは未完である。bounded Portal Certificate、fixture署名、test件数、negative coverageをClosureへ読み替えない。
