# 申告scopeと実resourceの結合

問いは「alphaの権限を持つ主体がscope=alphaと申告すれば、beta文書も読めるか」です。Identity・認証・認可のLEARNING_PATH §6実験1だけを扱い、固定合成resource属性に判断を結び付けて専用fixtureを実読取りします。

## 前提 → 予想 → 操作

subject/resource/action/scope、集合とAND条件を前提とします。authenticated_subject=Trueは合成入力仮定。Credential/token/IdPは検証しません。

1. 単元directoryで `python3 checker.py`。全有限真理表・内容bytes・保存command/source bindingを検算します。
2. `python3 -m http.server 0 --bind 127.0.0.1`。動的portのindex.htmlを開き、条件と予想を選び「比較する」。所有serverだけ終了します。
3. 正常/故障版のdecision/reason/read_count/contentを比べ、traceでdecision→read-start→read-completeの順序を確認し、答えを開きます。条件変更で予想・結果・答えreset。
4. 再実測は明示 `python3 runner.py --record`。専用TemporaryDirectoryに合成2文書をcopyして実読取りし、原票/command/fixture bytesを新observationsへ保存。旧runを保全し、tmpはcleanup。引数なしrunnerは書かずexit1で案内します。

予想はalpha主体のalpha文書readがallow/読取1。scope=alphaと申告してbeta文書を指定すると、正常版deny/読取0、resource所属との結合を省くscope-only故障版allow/読取1です。故障版の合成beta内容が実際に返ることを対照で観察します。

## 有限全真理表と入力境界

3主体（a-reader:alpha/read、a-no-read:alpha/なし、b-reader:beta/read）×2申告scope×2文書×2操作(read/write)＝24条件を全列挙。各条件で正常版と故障版を独立評価します。expected-table.jsonの24対をproducer実行前に手書き固定しました。

正常版の許可は、申告scope＝信頼resource所属 AND subjectのscope割当一致 AND requested action=readかつread許可。ownerは信頼表にあり必須ですが、owner一致・ownershipによる追加許可はこのルールに含めません。全体で正常allow2・deny22、故障allow4・deny20、実読取は正常2回・故障4回です。

| 要求 | 正常版 | scope-only故障版 |
|---|---|---|
| a-reader / alpha / doc-alpha / read | allow, read1, alpha内容 | 同じ |
| a-reader / alpha / doc-beta / read | deny-resource-scope, read0 | allow, read1, beta内容 |
| b-reader / beta / doc-alpha / read | deny-resource-scope, read0 | allow, read1, alpha内容 |
| read許可なし・write要求 | deny, read0 | deny, read0 |
| unknown resource・scope/owner欠損・未認証仮定等6入力 | expected refusal, read0 | expected refusal, read0 |

理由は入力境界→resource scope→subject scope→read permissionの優先順。故障版はresource scopeの拒否条件だけを省きます。未知resource、resource属性欠損、authenticated_subject=False/欠損、bool scopeを6拒否fixtureとして分けています。denyと入力評価拒否はどちらも読む前に停止しますが、同じ分類にはしません。

## 原典・実装・rawと独立照合

[NIST SP800-162公開Abstract](https://csrc.nist.gov/pubs/sp/800/162/upd2/final)でsubject/object/requested-operation/environment属性の関係を確認。PDF全本文は未確認。今回の必須owner/scopeと3つのAND規則は教材独自で、ABAC全体・標準適合を称しません。

experiment.pyは信頼固定表から対象属性を取得し、decisionがallowの場合だけ、owned tmp内のalpha.txt/beta.txtをPath.read_bytesで読む。ユーザー実file・Credentialへ入力resourceを直接path化しません。実IO後のbyte長/hex/SHA256/contentとreadcountをtraceに保存します。scope-only版も同じ専用合成fixtureだけを読めます。

checker.pyはproducerをimportせず手書き24対へdecision/reason/readcountを照合し、別literal `ALPHA SYNTHETIC DOCUMENT\n` / `BETA SYNTHETIC DOCUMENT\n`から期待byte/hex/hashを計算します。順序・拒否時readイベント不在、6入力境界、command stdout/exit、source/artifact digestも検査。5つのin-memory故障原票を検出し、rawを変更しません。

UIは保存run比較で、閲覧時の新認可・読取りではありません。[QA](qa/README.md)に実IAB/capture/read-only証拠。Skillはskills/atlas-resource-scope-enforcement/SKILL.md。正常7/未対応4routeは構造検査のみ、モデル挙動は未評価。

## 答え → 実務判断

申告scopeだけの一致では、選ばれたresourceとの結合が保証されません。対象属性は信頼側から取得し、対象と操作を認可した後で取得を強制する必要があります。allow判定だけでなく、deny時に読取りが起きないことも観測します。

今回のtraceは固定逐次実装の順序を示すだけです。判定後の属性変更/TOCTOU、実processのOS権限、IAM/IdP、ネットワーク分離、ABAC全体は保証しません。合成fixtureは公開教材用で、故障版の越境も個人情報の取得ではありません。

## 次coverage（未実行）

1. 4role菱形継承とcycle拒否を独立到達集合oracleへ照合。
2. fake clockで失効後のTTL cache・revision再評価・cacheなしを比較。
3. 合成token claimsのactive/exp/aud/actionの境界を手書き表へ照合。実署名・IdP認証は別。

Core/fullGate/commit/push/公開はこのローカル割当外で未実行。分野全体・Atlas全体のcompleteを主張しません。
