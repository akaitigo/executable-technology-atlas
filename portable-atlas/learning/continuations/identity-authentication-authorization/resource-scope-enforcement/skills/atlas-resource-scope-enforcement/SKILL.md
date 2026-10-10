---
name: atlas-resource-scope-enforcement
description: 合成fixtureの有限認可教材で申告scopeと信頼resource属性を結合し、判断前後の実読取と故障対照を検算する。実IdP/IAM/OS権限やABAC全体保証には使わない。
---
単元内READMEとcontracts.jsonを読み、route.pyの7入口へ依頼を対応づける。UIの予想→正常/故障版decision→readcount/content/trace→答えを辿る。
authenticated_subject Trueは入力仮定。Credential認証の実行証拠にしない。owner属性は必須だがowner一致は今回のpolicy条件ではない。
checker.pyは全有限真理表と別literal byte oracleのread-only検算。通常runnerは書かず、再記録の明示依頼だけrunner.py --recordを使う。runner所有tmpの合成alpha.txt/beta.txt以外へ読取経路を拡張しない。
unknown/missing attributeのexpected refusalとpolicy denyを分け、両方で読取0を確認。scope-only故障版はresource所属との結合を省いた対照。
IdP認証、OS権限変更、TOCTOU保証、ABAC全体適合は未対応としてREADME次coverageへ案内する。実Credential・実service・新権限・公開・課金をこのSkillから推定しない。
