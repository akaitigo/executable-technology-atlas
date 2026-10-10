# Identity・認証・認可を学ぶ道筋

この文書は[固定policyの既存教材](README.md)から、入力Identityの信頼、resourceへの権限、失効の時間境界へ進むための補足です。有限教材の補足であり、分野全体の学習完了を示すものではありません。以下の次実験はすべて未実行です。

## 1. 前提と主要概念

集合、辞書、graphの到達可能性、条件のAND/ORを理解してから、subject（要求する主体）、resource（対象）、action（操作）、scope（権限の適用範囲）を区別します。実装の読解にはPythonの関数とlist/dictが役立ちます。

学ぶ順序は **Identityの識別 → 認証の根拠 → 認可policy → role・属性・関係 → resourceへの強制 → 失効・session・監査** です。既存教材はこの中の固定認可policyだけを実行しています。

- 識別子があること、Credentialで本人性を確かめること、操作を許すことは別です。
- RBACではroleの権限とsubjectへの割当を分け、継承で得る権限を辿ります。role名だけでscope越えを許しません。
- ABACではsubject/object/operation/environmentの属性も判定材料になります。既存の文字列scope一致とは異なるモデルです。
- policy判定と、その判定を実際のresource取得・更新に適用する処理を分けます。判定器がallowを返しただけでは実アプリのアクセス制御を証明できません。
- grant削除、role割当削除、session終了、token失効は違う操作です。反映されるpolicy版と時刻も記録します。

## 2. 予想から既存実測へ

[UI](index.html)の4表示を予想してから、[model.py](model.py)、[原票](evidence/observation.json)、[環境・source binding](evidence/verification.json)を読みます。この文書作成では認可modelを再実行していません。

| 入力と変更 | 保存済み実測 | 読み取れること |
|---|---|---|
| alphaのeditorがreadを要求 | allow / `inherited_permission` | editor→viewer→document.readの継承 |
| 同じsubjectがbetaへ要求 | deny / `scope_mismatch` | assignmentのscopeを持ち出せない |
| viewerのread grant削除前 | allow | policy-v1の判断 |
| grant削除後の新snapshot | deny / `permission_not_granted` | 新policyを使う判断は変わる |

正常系は許可の根拠を継承まで辿れることです。越境やgrant削除後のdenyは意図した拒否です。READMEには未認証入力、unknown action、scope越え、hierarchy cycleのnegative検査が記載されています。cycleは`ValueError`で評価を拒否する境界であり、保存原票の通常denyと同一の返却形式ではありません。

`authenticated_identity: true`は入力仮定です。実装はCredentialやtokenを検証せず、resource識別子をrequest・decision IDへ記録しても、resourceの所属scopeやownershipを照合しません。grant削除は旧policyを破壊せず新snapshotを作りますが、cacheや分散伝播の遅延はありません。これらが、この教材を実認証・実製品の保証へ広げられない理由です。

[QA](QA.md)は過去のHTTP経由IAB操作を記録しています。favicon修正後の再読込と直接file表示は未確認と記載されており、この補足ではその空白を埋めた扱いにしません。

## 3. 実務で何を判断するか

実アプリでは信頼できる認証結果を入力にし、resourceの所属・所有者を信頼できる側から取得し、その対象と操作について認可を強制します。呼出側が書いたscopeだけを照合すると、対象のすり替えを取りこぼす可能性があります。

権限変更を扱うときは、どのpolicy版で判断したか、cacheの鍵と期限、失効の伝播、長時間処理の再判定点を決めます。役割の継承や属性ルールは説明可能なtraceを残し、欠損属性・未知action・評価不能を成功扱いしない契約を明示します。認証方式やOAuth/OIDCを選ぶ判断には別のprotocol・脅威model・製品検証が必要です。

## 4. 一次資料への道筋

| 原典とlocator | 読む目的と確認範囲 |
|---|---|
| [NIST RBAC unified model](https://www.nist.gov/publications/nist-model-role-based-access-control-towards-unified-standard)、Abstract / 論文§2.2 | role継承の既存binding。今回はリンク先論文を再取得していない |
| [NIST IR 6192](https://csrc.nist.gov/pubs/ir/6192/final)、Abstract / role hierarchy discussion | 階層roleの既存binding。今回は本文を再取得していない |
| [NIST SP 800-162](https://csrc.nist.gov/pubs/sp/800/162/upd2/final)、公開ページAbstract | ABACのsubject/object/operation/environment属性。公開ページを確認、PDF全本文は未確認 |
| [RFC 7662](https://www.rfc-editor.org/rfc/rfc7662.html)、§2.2 Introspection Response / §4 Security Considerations | active、scope、exp、audなどのresponseとcacheによる失効情報の遅れ |
| [RFC 9700](https://www.rfc-editor.org/rfc/rfc9700.html)、§2.3 Access Token Privilege Restriction | access tokenの権限とaudienceの限定。OAuth/OIDC実装とは別に読解する |

既存のlocatorは[sources.json](sources.json)にあります。次実験のローカルルールは作者が定める説明用Subsetで、標準適合やIdP相互運用を称しません。

## 5. 具体的な未教材coverage

| 未教材 | 次に区別したいこと |
|---|---|
| Credential発行・検証・更新、MFA、WebAuthn | 認証根拠の偽造・盗用・回復・失効への対処 |
| OAuth/OIDC・federation・session | issuer、audience、nonce等のprotocol上の意味と検証 |
| resource所属・ownership・ABAC | 入力scopeと実対象の結合、属性の取得元と欠損 |
| ReBAC・capability・職務分離 | 関係や委譲、組合せ禁止を含むpolicyの表現 |
| 分散失効・cache・TOCTOU | 新policyがどの要求から効き、判定後の変更をどう扱うか |
| policy管理・監査・製品相互運用 | 誰が権限を変更でき、評価不能をどう伝え、実製品で強制するか |

## 6. 次の実験案（4本、すべて未実行）

1. **resource属性と要求scopeを結び付ける。** 合成resource表にalpha/betaの所属とownerを置き、ローカルルールを「要求scope＝resource所属、subjectのscope割当あり、read許可あり」と明示します。alphaを名乗ってbetaのresourceを要求する負例、属性欠損、未知resourceを加えます。予想は同じroleでも対象を替えるとdenyになることです。入力の全組合せを小さな手書き真理表に照合し、判定traceのどの条件で拒否したかを保存します。原典はSP 800-162 Abstractです。これはABAC全体の実装ではありません。

2. **継承graphの分岐とcycleを区別する。** 4roleの菱形graphを作り、同じ祖先を2経路で辿る正常系と、逆向きedgeを加えたcycleを比較します。予想は正常系で到達roleを重複なく集め、cycleでは評価を拒否することです。全edgeから別方式で到達集合を求めるOracleと照合し、直接権限・継承権限・未知role・例外の扱いを明示します。原典は既存RBAC資料のhierarchy locatorで、実装前に論文該当本文を改めて確認します。session内のrole活性化や職務分離は残ります。

3. **失効後に古いcacheが残る時間を測る説明modelを作る。** 仮想時計でt=0に旧policyのallowをcacheし、t=3でgrantを削除、t=4と期限t=10に再要求します。期限境界は「現在時刻がexpiry以上なら無効」と固定し、TTL cache、新revisionで再評価する方式、cacheなしを比較します。予想はTTL方式だけがt=4で旧allowを返し得ることです。時刻・cache key・policy版・decisionを表で照合し、revoke時刻と有効化時刻の差を保存します。RFC 7662 §4はtoken introspection cacheの原典であり、このpolicy cache案への接続は類推です。実network・token失効の測定ではありません。

4. **token風の合成claimsで期限・audience・scopeの境界を読む。** 実Credentialを作らず、`active`、`exp`、`aud`、許可actionを持つ合成recordを入力にします。仮想時刻を固定し、正しいaudience、別audience、expiry直前・同時刻、inactive、欠損claimsを手書き期待表と比較します。予想はroleを持っていても期限・対象・actionのどれかが外れれば拒否することです。RFC 7662 §2.2とRFC 9700 §2.3を読み、標準の語彙とこの実験独自の必須項目を分けます。署名検証、発行者の信頼、HTTP endpoint、OAuth/OIDC flowは未実装のままです。

## 7. 資料の取得・検証状況

2026-10-05にSP 800-162の公開ページとRFC 7662 / RFC 9700のHTML本文を取得しました。`https://www.rfc-editor.org/rfc/rfc9700`は取得時にInternal Errorとなり、上表の`.html` URLで本文を確認できました。取得失敗は元URLの廃止を示しません。既存RBAC資料はmetadataとbindingを読み、今回の本文再検証とは区別しています。第三者本文・実Credential・個人情報は保存していません。

追加したのはこの文書だけです。認証・認可runtime、checker、UI、global gateは実行せず、既存原票・QA・digestを更新していません。次実験の予想は新たな実測証拠ではありません。
