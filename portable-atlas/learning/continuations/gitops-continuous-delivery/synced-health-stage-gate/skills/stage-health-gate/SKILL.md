---
name: stage-health-gate
description: 有限Python模型でSyncedとhealthを分け、2段階gateと新generation rollbackを検査する。実Argoや復旧保証には使わない。
---

このdirectoryでREADME→手表→runner→独立oracleを読む。python3 -B verify.py / route.py は実再計算するが保存しない。明示recordは未使用attemptだけ、sealはQA後一度だけ。health JSONの予想→実行→比較→原典→答えを確認し、開いた答えから全予想変更とinputreset、位置拒否保持、旧応答拒否を検査する。実Argo、probe、DBrollback、availability要求は未対応と明記し、関連data互換教材へ案内する。global installしない。
