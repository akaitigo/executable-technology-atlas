# 実行可能技術アトラス

97 Subject Atlasの固定ReleaseからManifest、Mastery、Coverage、Evidence、Skill Package、Completion Certificateを検証・探索する日本語Read Modelです。個別技術の知識は複製しません。

## ローカル実行

```bash
npm ci
npm run import
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

実在する署名済み公開Releaseは現時点で0件です。7件のfixture署名付き候補は完成証明ではなく、取込・検索・失敗Fallbackを再現するための固定入力です。

## 完成と信頼の境界

- Subjectは固定Releaseの署名、Digest、Core v1横断契約、Completion Certificateを検証し、公開用Trust Keyに固定された`complete`だけを公開完成と数えます。
- `planned`、`active`、`incomplete`、Releaseなし、隔離を同じ完成状態に丸めません。Coverageの`excluded`、`infeasible`、`expired`も既定で表示します。
- Portal Repositoryは[GitHub PUBLICのmain](https://github.com/akaitigo/executable-technology-atlas)を正本とします。Portal自身の`evidence/completion-certificate.json`とSubjectの公開完成数は別軸です。
- `npm run gate`はPortal契約、Evidence、SBOM、Release署名、DCO、証明対象Commitを検証します。Core正本の`atlas audit`と`atlas certificate verify`も完成条件です。

## Continuous Integration

`.github/workflows/publication.yml`は、全pushと`main`向けPull Requestをクリーンな`ubuntu-24.04` runnerで検証します。GitHub公式Actionはcommit SHA、Node.jsとGoは完全Version、Core v1は`cf9e6e2d…`へ固定し、npm依存は`package-lock.json`だけから`npm ci`で導入します。

Workflowの権限は`contents: read`のみで、秘密情報、永続Credential、依存Cacheは使いません。固定IndexとRouter Evalの再現一致、24件以上のTest、Lint、Build、Publication Gate、Core Audit、Certificate再検証を通し、runner内で追跡対象ファイルが変わった場合は拒否します。
