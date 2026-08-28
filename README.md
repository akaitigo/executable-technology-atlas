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
