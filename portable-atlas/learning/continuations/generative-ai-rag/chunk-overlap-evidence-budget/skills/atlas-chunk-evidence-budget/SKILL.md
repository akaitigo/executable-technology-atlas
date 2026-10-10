---
name: atlas-chunk-evidence-budget
description: 固定原文span・chunk境界・overlap・重複文字予算でretrieval hitとcontext支持を分ける。token/embedding/LLM/意味的支持/攻撃耐性には使わない。
---

rootは ../..。READMEの前提と元Subject/IRとの別scopeを読む。固定ASCII3原文とgarden[16,36)の単一chunk literal支持契約。正常支持/不支持、hit-only故障、期待入力拒否を分ける。

rootで `python3 -B skills/atlas-chunk-evidence-budget/route.py chunk-budget` は保存原票をread-only照合。実行はrunner.py --caseまたはserver.py UI。fresh原票は明示runner.py --recordのみ。

hit、完全span保持、retrieved完全span、included context支持と重複費用を別に読む。予想/条件変更と実行失敗で旧結果を使わない。

embedding / llm / tokens / semantic-support / security-guaranteeは未対応、READMEの境界/次案へ戻る。既存教材や全Gateを書き換えない。
