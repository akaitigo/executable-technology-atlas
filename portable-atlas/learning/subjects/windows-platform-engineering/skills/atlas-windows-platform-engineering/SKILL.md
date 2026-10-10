---
name: atlas-windows-platform-engineering
description: Run or inspect this finite Windows quoting argument-tail model using its existing runner, checker, character trace UI, and sources. Does not execute Windows APIs or shells.
---

module rootで `python3 -B route.py TOPIC`。既存の有限模型だけに案内。

- `quoting` → [runner.py](../../runner.py): defaultまたはSPEC準拠`--input-json`。模型accepted0、input/subset拒否2。
- `verify` → [checker.py](../../checker.py): read-only検査。
- `character-trace` → [index.html](../../index.html): [preview.py](../../preview.py)の一時URL、予想/字符step/比較。owned server/tabは終了後清掃。
- `sources` → [SOURCES.md](../../SOURCES.md): API/CRT/模型scopeを区別。

Windows API/CRT/VM、argv[0]/Unicode/全quote互換、shell/実process/install/権限はunsupported。[COVERAGE.md](../../COVERAGE.md)へ案内。原票更新の要求にだけobserve明示optionを使い、normal検査で更新しない。入力をeval/commandへ渡さず、global install/scope拡大をしない。
