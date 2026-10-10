---
name: atlas-android-platform-engineering
description: Run or inspect this local finite Android lifecycle and saved-state lesson using its existing runner, checker, and UI. Does not install SDKs or operate Android devices.
---

このmoduleの既存機能へ案内する。module rootへ移動し `python3 -B route.py TOPIC` で確認。

- `lifecycle` → [runner.py](../../runner.py): default caseまたはSPEC準拠の `--input-json`。accepted0、拒否2。
- `verify` → [checker.py](../../checker.py): read-only検査。
- `diagram` → [index.html](../../index.html): [preview.py](../../preview.py)の一時127.0.0.1 URLで予想/step/counter比較。終了時owned server/tabを閉じる。
- `sources` → [SOURCES.md](../../SOURCES.md): 公式contractとmodel仮定。

SDK/device/emulator/install/APK/OS kill/permissions/全Subject完成はunsupported。[COVERAGE.md](../../COVERAGE.md)へ案内。原票更新はユーザーが要求した場合のみobserveの明示option、normal verifyで更新しない。global installや新実装へscopeを拡げない。
