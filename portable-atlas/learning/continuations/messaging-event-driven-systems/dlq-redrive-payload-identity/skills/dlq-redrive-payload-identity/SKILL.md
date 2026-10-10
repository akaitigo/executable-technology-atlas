---
name: dlq-redrive-payload-identity
description: この有限SQLite教材のpoison backoff/DLQ履歴/redrive attempt/inbox payload identityを直接SQLと保存原票で検査する限定Skill。
---

# DLQ redriveとpayload identity

このmoduleだけで使う。実broker、durability、外部effect、ID変更による業務重複回避を保証しない。

1. README/oracle.jsonで0/1/3 attempt、tick−1 seed、4/5/7 redrive、same-ID契約を読む。
2. python3 -B route.py inspect で独立literal SQLを照合。consumer/driverをcheckerで共有しない。
3. python3 -B route.py lesson で未適用修正、既適用同payload、変更conflict、ID-only故障、拒否/失敗を予想。
4. 元DLQ保持、新attempt/source_dlq、inbox/effect/account、model ackを分けて説明。
5. 明示再実行依頼がある場合のみ python3 -B route.py record。通常checkは原票を更新しない。

旧教材・Portal・global Skillを変更しない。失敗時に正常答えを補わない。
