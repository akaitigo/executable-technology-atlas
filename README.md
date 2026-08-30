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
npm run gate
npm run dev
```

`http://localhost:3000`を開きます。既定fixtureは完全にオフラインで再現できます。

## CLI

```bash
node scripts/atlas-portal.mjs search ゼロトラスト
node scripts/atlas-portal.mjs import
node scripts/atlas-portal.mjs verify
```

組込Indexで検証できる署名済み公開Releaseは現時点で0件です。7件のfixture署名付き候補は完成証明ではなく、取込・検索・失敗Fallbackを再現するための固定入力です。既知のSubject v1 Certificateは、公開固定Releaseとして取込まれるまで件数へ加えず、取込後も固定Epochの`bounded-historical`履歴として保持します。

## 完成と信頼の境界

- Core v1 Completion Certificateは固定Epochの形式的Closureを証明する`bounded-historical`です。Manifestが`complete`でもSubject Definitive完成とは表示しません。
- Subject Definitive完成への自動昇格はありません。公開Trust Keyと、確定したCore v2 Definitive Certificateを検証できるまで必ず未証明として扱います。
- `planned`、`active`、`incomplete`、Releaseなし、隔離を同じ完成状態に丸めません。Coverageの`excluded`、`infeasible`、`expired`も既定で表示します。
- Portal Repositoryは[GitHub PUBLICのmain](https://github.com/akaitigo/executable-technology-atlas)を正本とします。Portal自身のv1 `evidence/completion-certificate.json`もbounded証明であり、Subject Definitive完成数とは別軸です。
- Release詳細はDigest固定で保存し、同一SubjectのCertificate履歴を上書きしません。隔離が1件でもあれば生成Indexと詳細は更新せず、last-known-goodを維持します。
- `contracts/non-regression-baseline.json`は97 Subject、246 Target、45 Evidence、11 Failure scenarioをID単位で凍結します。削除、未証明のStatus格上げ、boundedのDefinitive表示、Failure不可視化、Evidence切捨て、集約による粒度低下をGateで拒否します。
- 正当なID置換は`contracts/non-regression-mappings.json`に旧ID→新ID、理由、情報保持、同等以上のEvidence方針を明示する必要があります。旧固定Release自体は履歴から削除できません。
- UI、Portal Manifest、Docs、Routerは中立な事実、Coverage、Evidence、制約、比較条件、実行結果だけを記述します。自己宣伝、人物評価、推薦を目的化する文言をGateで拒否し、作者namespaceはRepository URLなど技術的に必要な識別に限定します。
- Core Definitive Gate v2のSchema、Migration、CLIは`reference-atlas-core`正式main/CI成功commit `072d7ca77981f51754e824d70c6d4ecd55ea67e5`で確定しています。Portalは3 Schemaと[24段階のMigration正本](contracts/reference/MIGRATION_DEFINITIVE_V2.md)をbyte digestで固定し、Authority-derived inventory closure、Gap、除外・実行困難、実Runtime Profile、Migration、Gate結果を[取込境界](docs/DEFINITIVE_GATE_V2.md)に従ってread-only表示します。現在は97 Subjectすべての署名済みv2入力が未収集のため、全件を`subject-definitive-input-missing`として表示します。
- `frontend-behavior`は`frontend-behavior-atlas` commit `4a0b2df8…`の`FE_DEPTH_REFERENCE.json`を固定取込します。18軸中1 satisfied / 17 partial、status `incomplete`を軸別の分母・Proof・Gapとともに表示し、299 E2E Test等の成功をboundedまたはDefinitive完成へ読み替えません。
- Authority Human ReviewはFE commit `6c2cfa41…`の固定read-only exportと2 Schemaを正本入力にします。80 packet/deep-link、230 candidate projection、113 machine proposal、3 stale relock hold、human decision 0件をDigest検証し、機械proposalをHuman decisionとして表示しません。
- Portalは一次資料本文を複製せず、URL、locator、offset、digestを表示します。Decision候補も保存・送信しません。将来の書込みはCore共通API/Schemaへ分離し、reviewer、time、reason、`manual-primary-source`、source/tool/context digest、旧→新mappingが揃わない操作を拒否します。`defer`と選択前stale relockはpendingのread-only holdです。
- Evidence Dependency Graphは`reference-atlas-core`正式main/CI成功commit `072d7ca77981f51754e824d70c6d4ecd55ea67e5`のSchemaとGate契約へ固定します。各Subjectのinput changed/current、影響output、stale/current、rerun command/result/runtime identity、missing required output、Proof/Closure structure driftをread-only表示します。GraphまたはCore Gate結果がない現在のSubjectは`missing-required-output`のままで、digest更新だけを復旧や完成へ読み替えません。
- `npm run gate`はPortal契約、Evidence、SBOM、Release署名、DCO、証明対象Commitを検証します。Core正本の`atlas audit`と`atlas certificate verify`も完成条件です。

## Continuous Integration

`.github/workflows/publication.yml`は、全pushと`main`向けPull Requestをクリーンな`ubuntu-24.04` runnerで検証します。GitHub公式Actionはcommit SHA、Node.jsとGoは完全Version、Completion Certificate検証用Core v1は`cf9e6e2d…`、Evidence DependencyとDefinitive v2契約は正式main `072d7ca…`へ固定し、npm依存は`package-lock.json`だけから`npm ci --ignore-scripts`で導入します。

Workflowの権限は`contents: read`のみで、秘密情報、永続Credential、依存Cacheは使いません。固定Index、非後退結果、Router Evalの再現一致、全Test、Lint、Build、Publication Gate、Core Audit、Certificate再検証を通し、runner内で追跡対象ファイルが変わった場合は拒否します。
