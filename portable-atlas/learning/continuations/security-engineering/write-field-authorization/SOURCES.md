# Atlas｜書込fieldの原典と実装対応

[OWASP API3:2023 Broken Object Property Level Authorization](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/) の公式本文は2026-10-06に取得済みです。今回の書込側も同じ本文の次の箇所へ対応付けます。第三者本文や図は複製していません。

| 狭い参照箇所 | 読む関係 | 今回の実装 |
| --- | --- | --- |
| Is the API Vulnerable? の書込側 | objectの利用許可だけでは、全項目の変更許可にならない | write grantの後でfieldを検査 |
| Scenario #2 / #3 | 意図しない価格や状態などの変更という問題 | 架空id/status/tenant_idなどの禁止更新と対照。原典のサービスへの実攻撃ではない |
| How To Prevent の入力の自動結合・変更可能項目の制限 | 要求全体の一括代入を避ける判断 | bulk_assignと明示許可表を比較 |

途中検査での部分更新と全検査後の反映は、この小さなローカル実験の実装比較です。原典からDB transactionの保証を導いたり、OWASP全要件を実装したと扱ったりはしません。役割名・許可表・拒否番号は教材固有です。

前提は [object認可の本文](related.html?topic=object) → [読取field開示の本文](related.html?topic=read-field) → 今回のwrite grant/field → 拒否時副作用です。2資料の場所と内容hashは `related-sources.json` に固定し、元ファイルはread-onlyで表示します。

