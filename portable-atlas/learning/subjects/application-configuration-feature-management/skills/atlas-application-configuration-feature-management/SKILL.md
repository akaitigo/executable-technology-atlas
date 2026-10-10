---
name: atlas-application-configuration-feature-management
description: 架空のlayered typed configと固定actor feature rolloutの既存教材を使って優先順位・型・truthiness bug・拒否を比較する。
---
このmoduleの既存runner/checker/UIだけへrouteする。ルートはこのファイルの2階層上。
`python3 skills/atlas-application-configuration-feature-management/route.py config-flags` がread-only経路を表示する。
通常は `python3 runner.py` または `python3 checker.py`。原票更新は明示的に要求されたときだけ `python3 runner.py --record`。
UIは `index.html`。一時previewは `python3 preview.py`、確認後owned tab/serverを終了する。
未対応routeはexit2。envはJSONの架空入力であり実OS環境変数を変更しない。system config、外部provider、実SLA保証、secret manager認定を行わない。module外を変更しない。
