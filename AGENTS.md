# Repository instructions

- 日本語UIと利用者向け文書を正本にする。
- 個別技術知識をPortalへ複製しない。
- Subject Source Tree、Default Branch、Git submoduleをRuntime依存にしない。
- 未完成、除外、実行困難、失効、隔離を隠さない。
- `app/data/index.generated.json`はImporterで再生成し、手編集しない。
- completeを主張する前にCore `atlas audit`と`npm run gate`を通す。
