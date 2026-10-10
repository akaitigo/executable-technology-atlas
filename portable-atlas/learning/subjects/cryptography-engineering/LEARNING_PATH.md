# Cryptography engineeringを学ぶ道筋

この文書は[HMACと再送防止の既存教材](README.md)から、認証するbytes、freshness、鍵の運用を分けて学ぶための補足です。有限教材の補足であり、分野全体の学習完了を示すものではありません。以下の次実験はすべて未実行です。

## 1. 前提と仕組み

文字とbyte列、UTF-8、hex、JSON、hash、集合stateを理解します。意味が同じmessageでもserialized bytesが違えば、MACの入力は違います。

| 仕組み | 鍵と検査 | この教材との関係 |
|---|---|---|
| hash | 鍵なし、内容digestの照合 | SHA-256値を追跡に使う。自己整合だけで送信者を認証しない |
| MAC / HMAC | 共有秘密鍵でtagを生成・検証 | HMAC-SHA256の有限計算。公開fixture keyは本番の秘密ではない |
| 公開鍵署名 | 秘密鍵で署名、公開鍵で検証 | 未実装。HMACをデジタル署名と呼ばない |
| 暗号化 / AEAD | 機密性、AEADでは認証も扱う | 未実装。既存messageは読める |

学ぶ順序は **byte契約 → MACと検証 → envelope → replay/freshness → 鍵の識別・rotation → 暗号化・署名・鍵交換 → protocolと運用** です。MACが通っても、再送、認可、resource操作の成功を示しません。共有鍵を持つ双方がtagを作れるため、HMACを第三者への非否認証明にしません。

## 2. 予想から既存実測へ

[UI](index.html)、[runner](runner.py)、[独立vector Oracle](oracle.json)、[実行原票](evidence/observation.json)、[環境・digest](evidence/verification.json)、[QA](QA.md)を読みます。この文書作成では暗号計算・checkerを実行していません。

| 条件 | 保存済みMAC | 別のReplayGuard |
|---|---|---|
| 正常 | valid | 受入、IDを記憶 |
| message / key / tagの変更 | mismatch | state更新前に拒否 |
| 正常messageの再送 | 再びvalid | duplicate-idで拒否 |
| 短いtag / 非hex | invalid-tag-format | state更新前に拒否 |

7条件とRFC 4231の2vectorが記録されています。「MACだけで2回目を拒否」という予想はreplay条件で外れます。guardはMAC検証後にenvelope内の認証済みmessage_idを記憶します。scenarioごとに新stateで、replay条件だけ正常受入を先に行います。guardを作り直すと再受入できる境界はQAの検査記録であり、永続性はありません。

形式契約は同型bytesとfull 32-byte tagです。短いtagの拒否は全HMAC profileでの禁止を意味しません。認証された不正envelopeや重複JSON keyの拒否も別の入力契約です。`compare_digest`の利用は実装から確認できますが、timing測定や教材全体のconstant-time証明はありません。公開fixture keyを秘密扱いしていません。

## 3. 実務で何を判断するか

何を認証したいかを先に定め、操作・対象・送信者・request ID・protocol用途を曖昧なくbyte化します。tag検査前に未認証IDでstateを更新しないこと、検査後のID確認と記憶が同時要求に対して原子的であることも別に検査します。

鍵は用途・送信者・versionを区別し、配布、保管、rotation、失効、復旧を設計します。secretをログや教材原票へ記録する構成を本番へ流用しません。HMACは暗号化を代替せず、replay対策は時計・nonce/sequence・永続state・資源上限を含むprotocol設計です。標準primitiveを使った有限vector一致から実利用の安全性全体を結論しません。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的 |
|---|---|
| [RFC 2104](https://www.rfc-editor.org/rfc/rfc2104.html)、§1–2 / §3 Keys | shared-key MAC、HMACの構造と鍵の扱い |
| [RFC 4231](https://www.rfc-editor.org/rfc/rfc4231.html)、§4.2–4.3 / §5 | 既存2vectorと、個別用途の安全性主張との違い |
| [Python hmac](https://docs.python.org/3/library/hmac.html)、new / compare_digest | byte入力、比較APIの注意 |
| [RFC 4303](https://www.rfc-editor.org/rfc/rfc4303.html)、§3.4.3 / §3.4.4 | sequence検査とintegrity検査の区別。既存guardはESPではない |
| [RFC 8032](https://www.rfc-editor.org/rfc/rfc8032.html)、§5.1.6 Sign / §5.1.7 Verify | 公開鍵署名をHMACから区別する読解。未実装 |

既存bindingは[sources.json](sources.json)にあります。Python公開Docsは取得時3.14.8で、既存runtime版とは区別します。

## 5. 未教材の問いと次実験

| 未教材 | 問い | 次の入口 |
|---|---|---|
| serialization・用途分離 | 同じ意味と同じ認証bytesはどう違うか | 実験1 |
| replayの並行性・永続化・TTL | 再起動や同時要求でID記憶は何を防げるか | 実験2 |
| 鍵rotation・sender namespace | valid tagでも受入policyが異なるか | 実験3 |
| AEAD・nonce・鍵交換・KDF | 機密性や導出鍵に必要な条件は何か | 別原典・vector・実装検証が必要 |
| 公開鍵署名・PKI・TLS | 検証鍵の信頼と署名の意味は何か | RFC 8032から別教材へ |
| entropy・HSM/KMS・side-channel・PQC | 鍵とprimitiveの実運用をどう検証するか | この公開key教材では未評価 |

## 6. 次の実験案（3本、すべて未実行）

1. **意味と認証bytesの境界を比較する。** 公開test keyだけを使う独立fixtureで同じJSON値のkey順・空白を変え、raw-byte MACと明示canonical encoding後のMACを比較します。予想は前者のtagが違い、定めたcanonical規則では一致することです。期待byte列を先に固定し、重複key・数値表現・欠損fieldを拒否する契約も分けます。operation/resource/用途をMAC対象から落とした故障版で、変更が検出されない条件を列挙します。原典はRFC 2104のmessage入力です。canonical JSONは独自契約で、標準化済protocolや暗号安全性の証明ではありません。

2. **ID確認と記憶のatomic性を有限stateで比べる。** 同じ認証済みIDの2要求にcheck→rememberの手順を与え、全interleavingを列挙します。予想は別々のcheck/write版で二重受入があり、単一の不可分操作modelでは1回になることです。再起動時のmemory消失と保存stateからの復元も独立条件にし、受理数・state・拒否理由を手書きtraceへ照合します。MAC不正入力はstateを変えない条件を保持します。原典はRFC 4303のreplay/integrityの分離との対比であり、独自ID set modelです。実DB transaction、crash durability、ESP window適合は未実証です。

3. **鍵versionとsenderの受入policyを比べる。** 公開test用の旧/新keyと2つの架空senderを置き、鍵ID・sender・message ID・用途を認証対象に含めます。移行期間と終了後の許可表を固定し、valid MACでも旧key期限外・別sender・用途違いを拒否する期待表と照合します。予想は暗号検証結果とpolicy判断が別になることです。replay keyを単一IDだけにした衝突例と、senderを含めた場合も比較します。原典はRFC 2104 §3を入口にした独自運用modelで、鍵配布・secure storage・失効伝播・実時計は扱いません。

## 7. 資料の取得・検証状況

2026-10-05に上記RFC 4件とPython hmacのHTML本文を取得して参照箇所を確認しました。今回取得不能だったURLはありません。既存2vectorはoracle.jsonとの対応を読み、今回新しくvectorを実行した扱いにしません。第三者本文・本番key・Credentialは保存していません。

追加したのはこの文書だけです。MAC・署名・暗号化、checker、server、UI、global gateは実行せず、既存原票・QA・digestを更新していません。次実験の予想は新たな実測証拠ではありません。
