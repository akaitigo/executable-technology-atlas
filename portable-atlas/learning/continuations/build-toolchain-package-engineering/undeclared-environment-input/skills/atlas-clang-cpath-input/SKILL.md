---
name: atlas-clang-cpath-input
description: このMacの既存clangとowned banner.hでCPATH由来の隠れ入力とstale cache hitを調べる有限教材。本番buildのhermeticity、SDK更新、署名公開、他OSの保証には使わない。
---

教材rootはこのdirectoryから ../..。READMEの予想・5attempt・未網羅を読んで、cache hitと現在headerに適合したstdoutを分ける。

保存原票を調べる要求はrootで `python3 -B skills/atlas-clang-cpath-input/route.py cpath-cache`。独立checkerを実行し採用rawのbad-B=A、clean/good-B=Bを確認する。原典locator、key payload、実binary digestまで追う。

実再現は `python3 -B runner.py`、画面操作は `server.py`。既存clangを先に確認し、欠如をtoyへ置換しない。子processに全envを渡さず、owned fixtureだけを使う。新しい原票保存は明示 `--record` のみ。5attempt後にowned tempを終了する。

production-sign やcross-OS保証の要求は未対応として停止し、READMEのSDK/linker等の境界と次案へrouteする。実SDK更新、既存CPATH変更、署名・publishをこの教材に追加しない。
