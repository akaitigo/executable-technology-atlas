---
name: atlas-agent-call-authorization
description: Atlasの合成read/add教材で、型が正しい値と具体的な呼出しへの承認を分けて学ぶ。実LLM・外部操作・実ユーザー承認やOS権限の検証には使わない。
---

# Atlas — 呼出しへの承認を読む

最初に [README](README.md) と [契約](CONTRACT.md) を読み、JSON・型付き参照が必要ならREADMEの既存教材へ戻る。このSkillは学習用の案内で、現実の操作の許可を与えない。

1. 「toolが許可され、値が整数なら実行できるか」には [画面](index.html) のnormal/args-changedを案内する。4も100も型に合うが、固定承認のa=4と異なる100はadd前に拒否。read 1回・add 0回を [手表](hand-oracle.json) と保存結果で確認する。
2. 「期限ちょうど、別の計画やcallならどうか」にはexpiry-at/plan-changed/call-changedを案内する。期限はnow<10。call-changedは実callがadd-a、承認だけadd-otherなので、計画hashの不一致と分けられる。
3. 「観測にapprovedと書いてあるから許可にできるか」には同じ入力のmissing-grant/bad-data-approvalを対照する。故障の103は正常な承認ではない。外部固定承認を観測で置き換えており、authority_breachを確認する。hashを再計算しても出所の権限は増えない。
4. 「前回の値や使用済み承認を使えるか」にはstale-observation/consumed-grantを案内する。型が合う旧値もrequestが違えば拒否。未到達の照合はnull、authorized=falseは最終許可なしである。

予想→保存計算→正常と拒否／故障の比較→ [原典](SOURCE-MAP.md)・[実装](model.py)→答えの順を守る。記録の欠落・改変・別条件を試した後は、古い表・答え・開いた詳細が消えることを確認する。画面の確認結果は [GUI-QA](GUI-QA.md) を読む。

通常は保存結果を読む。[verify.py](verify.py) は [実行案内](observations/README.md) の保存先を指定して検査し、模型を再実行しない。新しい実行は別途調整した専用の短い枠と [CLI-POLICY](CLI-POLICY.md) の資源条件が必要。予想が外れたこと、期待した拒否、準備失敗を混同しない。

実ユーザー同意・署名・MCP/API接続・外部送信・OS権限・LLM防御・並行の原子的消費・耐久的再送の要求には、この模型で検証済みとは答えない。[COVERAGE](COVERAGE.md) の未対応へ案内する。新依存・サービス・共有repo編集は不要。
