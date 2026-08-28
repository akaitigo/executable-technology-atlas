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

現時点で実在する署名済み公開ReleaseとCompletion Certificateは0件である。7件のSubject bundleはtest-only鍵で署名した再現可能fixture候補であり、UI・Indexとも`fixture-only`として完成証明と分離する。
