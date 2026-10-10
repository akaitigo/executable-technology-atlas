---
name: incremental-corrected-batch
description: 保存された差分update/deleteの実SQLite教材を読む・照合する・明示時のみ新規記録する。
---

このmodule内の既存worker/runner/checker/UIのみを使う。
read-only入口は python3 route.py inspect、UI位置は python3 route.py lesson。
利用者が新規記録を明示した場合だけ python3 route.py record。旧runは上書きしない。
unknown routeはexit2。元Subject、他continuation、Portal、既存serverは変更しない。
event ID / row key / sourceVersion / input list順を区別する。
単一batchの再適用不変と順序入替の非可換、expected refusalとunexpected failureを区別し、実CDC/framework/exactly-onceと呼ばない。
