---
name: atlas-build-toolchain-package-engineering
description: stdlibの閉じたtiny build DAGとcontent cache、mtime-only stale hitを既存教材で比較する。
---
module内の既存runner/checker/UIだけへrouteする。ルートはこのファイルの2階層上。
`python3 skills/atlas-build-toolchain-package-engineering/route.py tiny-build` でread-only経路を表示する。
通常は `python3 runner.py` 又は `python3 checker.py`。原票更新は明示的な要求時だけ `python3 runner.py --record`。
UIは `index.html`、一時previewは `python3 preview.py`。確認後owned tab/serverを終了。
未対応routeはexit2。mtime操作はrunnerが生成するmodule-owned fixture input/outputだけ。既存sourceをtouchしない。外部package install、build publish、production toolchain再現性保証を行わず、module外を変更しない。
