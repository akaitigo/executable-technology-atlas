---
name: atlas-data-governance-quality-lineage
description: 固定neutral datasetの品質契約、lineage DAG、source hash変更によるcache失効を既存教材で比較する。
---
このmoduleの既存runner/checker/UIだけを使う。ルートはこのファイルの2階層上。
`python3 skills/atlas-data-governance-quality-lineage/route.py contracts-lineage` はread-only経路を表示する。
通常は `python3 runner.py` または `python3 checker.py`。原票再生成は明示的な要求時だけ `python3 runner.py --record`。
UIは `index.html`、一時previewは `python3 preview.py`。確認後にowned tab/serverを終了する。
未対応routeはexit2。実データ・PII・会社policy認定・PROV/CSVW準拠認定を実行したと扱わない。専用module外を変更しない。
