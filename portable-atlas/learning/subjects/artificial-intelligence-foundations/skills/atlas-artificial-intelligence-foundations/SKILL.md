---
name: atlas-artificial-intelligence-foundations
description: ローカル有限gridのBFSとA*探索で、最短route、Manhattan推定、過大推定、closed再開、同点順序、到達不能と入力拒否を再現する。実ML/LLM学習やAI分野全体の実装は未対応。
---

# 有限探索教材への限定入口

[README](../../README.md)の道筋と[UI](../../index.html)を読む。対象は単位costの4近傍grid。既存[runner](../../search.py)と[checker](../../verify.py)以外の新実装・外部API・依存追加をこのSkillの対応済み能力として扱わない。

実結果を求められたらmodule directoryで `python3 verify.py`。通常はread-onlyで[原票](../../observations/raw.json)と[receipt](../../observations/receipt.json)のsource digestを照合する。原票更新を明示要求された場合のみ `python3 verify.py --record`。UI実確認は `python3 serve.py --port 0` の表示URLを使い、自分のserver/tabを終了する。

[route.py](../../route.py)は `python3 route.py astar` 等で既存checker/UI/READMEを返す。bfs/astar/heuristic/reopen/tie/unreachable/invalidが正常route。それ以外、例 `python3 route.py llm-training` は未対応とし[coverage](../../coverage.json)の次の学びを案内する。これは作者routing smokeであり独立AgentEvalではない。

説明時はf=g+h、最初のgoal取り出し終了、goalを含むexpanded数、tie順、reopen設定を添える。過大推定100は意図的反例で最短保証がない。許容的非整合hはreopenで回復する本例とclosed固定の誤りを比較し、一般の性能保証へ拡張しない。到達不能と入力拒否を分ける。ML/LLM、確率計画、重み、CSPは[未教材](../../coverage.json)として明示する。
