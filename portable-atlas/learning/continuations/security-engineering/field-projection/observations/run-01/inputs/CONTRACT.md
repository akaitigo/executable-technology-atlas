# Atlas｜読めるレコードでも、全項目を返してよい？

## 目的と前提

目標73の object 読取と field（応答中の項目）の開示を分ける。既存の tenant・operation・grant の検査を前提に、object 許可後に全項目を返す対照と、role別の明示許可一覧から応答を組み立てる版を比較する。すべて架空データを使う Python 関数内の有限実験である。

上流が正しく認証して渡す `context={actor_id, role, tenant_id, read_grants}` と、保存した policy・record は信頼済みと仮定する。3 context はいずれも tenant-red 所属で red-report の read grant だけを持つ。context は利用者の request と別の引数であり、request で上書きしない。context自体を偽造できる相手はこの教材で防げない。

## 固定した項目と許可表

record は red-report / red-archive（同tenant、grantなし）/ blue-report（別tenant）の3個。項目順は `id, title, status, contact_email, internal_note, tenant_id`。

| role | id | title | status | contact_email | internal_note | tenant_id |
| --- | --- | --- | --- | --- | --- | --- |
| viewer | ○ | ○ | ○ | × | × | × |
| operator | ○ | ○ | ○ | ○ | × | × |
| auditor | ○ | ○ | ○ | × | ○ | × |

この表は教材固有の業務ルールで、役割名から一般的な権限を推測しない。object の許可は全role共通で red-report のみ。情報の匿名化やDBクエリの効率化を目的とする射影とは別である。

## 要求と失敗判断

要求は `object_id` と `operation` が必須、任意の `fields` だけを許す。operation は文字列 read のみ対応。fields省略はroleに許された全項目を返す。指定時は空でない重複なし文字列listで、既知の項目だけを受け付ける。順番はrecordの固定項目順へ揃える。禁止項目を1つでも要求した場合は、許可項目の部分返却もせず403・payload=null。

共通検査の順は request schema → trusted context → operation → object存在 → tenant → grant。schema不正は400、不明role/不正contextは401、未対応operation/越境/grantなしは403、不明objectは404。既知object間の存在情報やtiming保護は未実装。

共通検査に通った後、対照版 `object_only` は fields指定も開示表も使わずrecordの全6項目を返す。修正版 `projected` は上表を使い、省略時は許可全項目、指定時は要求項目が全て許可される場合だけ返す。この差だけを意図的な欠陥とする。全拒否の応答は `{status, reason, payload:null}`。関数はfixture/context/requestを変更しない。

## 実装前に固定する有限39条件

- 3role × 3object の fields省略9条件。
- red-report に対する3role × 6単一field の18条件。
- 境界12条件：不明role、request.role追加、未知field、別tenant値の追加、fields文字列、空fields、重複fields、不明object、write operation、object_id不足、contextなし、viewerがidとinternal_noteを同時要求。

red-report の通常3条件は対照が全6項目、修正版は3/4/4項目。単一field18条件の修正版は許可11・拒否7。object matrixでは各版3許可6拒否。境界の最後だけは対照が全項目を返し修正版が拒否し、他11件は双方拒否。固定全39条件の修正版は許可14・拒否25、対照は許可22・拒否17。元データの全項目や元の期待をhandlerへ渡して合否を決めず、handler結果は別の固定期待へ照合する。

## 原典・受入・Skill

[OWASP API3:2023](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/) の Is the API Vulnerable?（propertyへの読取権限）、How To Prevent（返す項目を明示し必要最小限にする）を2026-10-06に確認。Scenario #1 は過剰開示を読む参考。書込の mass assignment は今回実装しない。

実装前の許可表を独立担当にも渡し、別々に期待を作る。全39条件のstatus/reason/payloadのキーと値、拒否時payloadなし、入力不変、取得失敗/改変/古い応答で画面の旧結果消去を確認する。画面は保存したPython結果を読むもので、ライブAPIや外部通信の実験ではない。Skillは通常閲覧・禁止field要求・認証実装要求の3問を資料から辿る有限利用に限る。

実認証、JWT、HTTP handler公開、DB、並行更新・分散強制、write mass assignment、一般の安全認証は対象外。既存AppSec・privacy・DB単元の再加算はせず、作者の加算は0、全体判断は親担当に委ねる。
