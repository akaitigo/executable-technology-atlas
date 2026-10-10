---
name: as-of-history
description: この固定教材の整数時刻as-of JOINとlatest故障例を、保存SQLite観測と独立注文台帳で再確認する。
---

この教材だけで使う。READMEの前提と時刻契約を読み、通常 `python3 -B verify.py` と `route.py` を実行する。予想→条件→注文IDの版→raw SQL→答えの順で学ぶ。gap/unknownを失わず、multiple-matchとEXECUTION_FAILUREを正常集計に変換しない。checkerは読み取り専用。記録を更新するなら未使用attemptと明示承認の範囲を確認する。本番DWHや遅延訂正を保証しない。
