---
name: atlas-agentic-systems
description: 固定planとdummy read/addの有限状態機械を再現し、allowlist・引数・budget・loop・end・errorとtool result出所の境界を比較する。AI推論、LLM自律plan、外部tool、実agent基盤は未対応。
---

# 有限tool-plan教材への限定route

[README](../../README.md)の道筋と[graph UI](../../index.html)を読む。既存[machine](../../machine.py)、[checker](../../verify.py)、[route](../../route.py)へ限定する。AI推論や外部toolを動かしたとは説明しない。

module directoryで `python3 verify.py` はread-only。[receipt](../../observations/receipt.json)のsource/input/tools digestを照合して[raw](../../observations/raw.json)を引用する。原票更新を明示要求された場合だけ `python3 verify.py --record`。実IABは既存 `python3 serve.py --port 0` の実startup URLを開き、自作tab/serverを終了する。

`python3 route.py budget` が正常。state-machine/tool-allowlist/budget/loop/end/error/result-boundary/auditが対応。`python3 route.py llm-agent` 等は未対応とし[coverage](../../coverage.json)を案内する。これは作者routing smokeで独立AgentEvalではない。

data-onlyはtool resultのproposed_planを無視し、著者planのadd(4,3)→endで7。promote-resultは意図的に差替え、add(4,100)→endで104。両方ともdummy allowlistを使い、文字列evalや外部actionは行わない。authoredはtoyの出所flagで実ユーザー承認ではない。

endも1step。tool call数/audit edge数とcommand budgetを分ける。予算不足で値7があってもENDEDではない。loop拒否は繰返しstate検知であり、無限実行を放置した証拠ではない。tool error、入力拒否、明示end欠落を別結果とする。[原典](../../sources.json)と次の未教材を案内し、本番の権限・防御保証へ拡張しない。
