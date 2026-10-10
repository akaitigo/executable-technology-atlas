# Atlas｜原典と今回の実装

2026-10-06に [OWASP API3:2023 Broken Object Property Level Authorization](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/) の著者本文を取得して確認しました。本文・図・第三者コードは複製していません。

| 原典の狭い参照箇所 | 今回読む関係 | 実装・記録 |
| --- | --- | --- |
| Is the API Vulnerable?、読取側の最初の箇条書き | objectへのアクセス許可と個別項目の読取許可を分ける | `handler.py` のobject検査後のfield-allowlist |
| Scenario #1 | 応答の余分な情報が開示になる例 | 架空recordのcontact_email/internal_note。原典のサービスを再現した実攻撃ではない |
| How To Prevent、返す項目を明示する説明と必要最小限の説明 | 全recordのコピーから許可項目の組立てへ | `object_only` と `projected` の保存応答を比較 |
| 書込の説明とschema-based response validation | API3には今回より広い内容もある | write側のmass assignmentや汎用schema validatorは未実装 |

役割名・許可表・拒否番号・要求形式は教材固有です。OWASPがこのfixtureや番号を規定したとは扱いません。原典全要件やASVSレベルへの合格も主張しません。



既存object認可とTOCTOUの元資料は [読取viewer](related.html?topic=object) / [TOCTOUの読取viewer](related.html?topic=toctou) から開けます。2ファイルの場所と保存時hashは `related-sources.json` で固定し、内容が変わった場合は表示を止めます。
