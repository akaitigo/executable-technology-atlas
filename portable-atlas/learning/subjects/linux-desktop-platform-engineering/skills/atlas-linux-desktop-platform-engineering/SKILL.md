---
name: atlas-linux-desktop-platform-engineering
description: このAtlasのDesktop Entry有限parser教材を既存runner/checker/UIで実行し、Exec quoting、%f/%F/%%、単純splitの反例を比較する。Linux GUI起動や設定変更には使わない。
---

教材rootはこのファイルから `../..`。README.mdのsubset、学習の道筋、未教材coverageを読む。
正常は `python3 -B run.py`。単一file比較は `--case single --selection spaces`。escapeは `--case dollar`。未知fieldは `--case unknown`。shell禁止は `--launch shell`（JSON rejected、exit2）で確認する。
独立手token oracleは `python3 -B check.py`。UIは `python3 -B server.py` の所有loopback URL。予想→操作→trace/argv→原典/実装→答えを確認し、所有serverを終了する。通常checkerはread-only。原票更新の依頼がある場合だけ `check.py --record`。
既存runner/checker/UIだけにrouteする。Desktop Entryをinstallしない、Execをprocess/shellとして実行しない。実Linux GUI・X11/Wayland・D-Bus要求は未教材coverageと区別する。新runner、新依存、OS設定を作らない。
