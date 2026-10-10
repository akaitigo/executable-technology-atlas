# Atlas｜拒否したのに、値が変わっていない？

## 目的・前提・書込許可

目標73と前教材の残不足「書込側field許可・拒否時store不変」に対応する。読めることから更新権限を推定しない。別引数の信頼済み `context={actor_id,role,tenant_id,read_grants,write_grants}` を仮定し、`read_grants` は更新の許可に使わない。既存教材のファイルは変更せず、独立した架空storeを使う。

| role | read grant | write grant | 書き込める項目 |
| --- | --- | --- | --- |
| viewer | red-report | なし | なし |
| operator | red-report | red-report | title, contact_email |
| auditor | red-report | red-report | internal_note |

この役割表は教材固有で、一般の職務や上下関係を表さない。全roleはtenant-red所属。red-archiveは同tenantでもwrite grantなし、blue-reportは別tenant。id・status・tenant_idは誰も書込不可。read側のfield許可とwrite側の許可を混同しない。

## 要求・番号・応答

request は `object_id, operation, changes` の3キーのみ。object_idは空でない文字列、operationは文字列、changesは空でないdict。6個の既知fieldだけを受け付け、値は1〜80文字の文字列とする。これは本物のメール形式検証やJSON parserではない。重複JSONキー、nested値や巨大入力は対象外。

共通検査は request schema → trusted context → operation → object存在 → tenant → write grant。各条件は先に止まった理由を返す。schema不正400、contextの型不正/不明role401、update以外のoperation403、不明object404、tenant不一致403、write grantなし403。番号はPython関数模型の規約であり、実HTTPや本人確認の実装ではない。全拒否のpayloadはnull。

成功応答は `payload={object_id:要求先ID, accepted_fields:要求field名の配列}`。元record全体や値は返さない。accepted_fieldsは今回受け付けた指定項目で、全storeの更新保証を代用しない。request/contextはどの方式も変更しない。

## 3方式と2つの失敗

1. **bulk_assign**：共通のobject検査後に一括代入する。field許可を省く意図的な対照。
2. **incremental_check**：changesの挿入順でfield許可を確認し、その場で値を更新する。後半の禁止項目で403を返しても、先行した許可項目の変更が残り得る対照。
3. **validate_then_apply**：全fieldが許可されるか先に検査し、候補recordを作ってから対象recordを置き換える。禁止項目が1つでもあれば403でstore全体を変えない。

今回のPython dictの挿入順を固定し、許可→禁止と禁止→許可の2条件を対照にする。要求の順番に依存せず拒否時不変であることを修正版の受入とする。DB transaction・並行atomicity・永続化・例外やプロセス停止後の回復を実証したとは呼ばない。

## 実装前の24条件と受入

4正常（operatorのtitle/contact/両方、auditorのnote）、read-only viewer、同tenant無write grant、cross tenant、不明object、禁止note、許可と禁止の2順序、auditorの禁止title、保護id/tenant/status、未知field、不明role、request.role追加、request.tenant追加、値型不正、空changes、operation違い、contextなし、changesのlist型。case ID・要求・各方式のstatusとstore差分は実装前に `cases.json` と `expected.json` へ固定する。

bulk_assignの成功は11/24、後2方式は4/24。incremental_checkだけ、許可title→禁止internal_noteの1拒否条件でtitleの変更が残る。修正版は全拒否20条件でstore全体不変。正常4条件は指定した許可fieldだけを対象recordで変更し、他field・他recordを変えない。診断用before/after storeは応答payloadとは別に保存する。

独立担当がproducer読取前に作る期待へ、全72応答のstatus/reason/payloadと全storeのbefore/after、context/request不変を照合する。保存した表示を読む画面では予想→操作→比較→原典/実装→答え/限界を用意し、古い答えの消去も確認する。Skillはread許可とwrite許可、混在要求の部分更新、DB原子性を問う有限3例に限定する。

## 原典と範囲

[OWASP API3:2023公式](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/) は2026-10-06に本文取得済み。Is the API Vulnerable?の書込側、Scenario #2/#3、How To Preventの入力の自動結合と変更可能項目の制限を読む。今回はOWASP全要件、実認証/JWT/HTTP/DB/分散強制/実製品安全認定を実装しない。上流context・policy・storeは信頼する仮定。旧教材・共有台帳はread-only、作者の加算は0。
