# account認可とnonce：同じnonceの別txIDを分ける

元[hash/linkと残高教材](../../../subjects/decentralized-systems-blockchain/README.md)の認可/nonce次案を深掘りする有限unitです。hash整合と残高→本認可/入力順→NIST原典と未教材の署名・consensusの順に読みます。元Subject・旧unit・Portalは凍結、入口追加0、Subject/Atlas incompleteです。

## 予想→実操作→比較→原典→答え

前提は整数、txID、before/after状態。既存Mac Python stdlibのみ、installなし。

~~~sh
python3 -B server.py
~~~

動的127.0.0.1 URLを開き、採用件数・A残高・A nonceを予想。条件を選び「認可・nonce・残高を検査」を押します。順番ごとの実tx・actor・nonce・amount、採否、before/afterの全state、最終残高を比較。原典・実装・原票を読んで答えを開きます。答えはactualの各decision・残高・nonceと採用件数から生成し、case名だけで結論を置きません。予想3項目を変えると新値と他の予想を保持し、旧答え本文を空にして閉じます。条件変更は予想unknownへ。実行開始・失敗・遅着旧応答も旧比較を使いません。所有serverだけCtrl+Cで終了。

## 事前の有限契約と手計算表

[fixtures](fixtures.json)と[独立literal表](hand-oracle.json)をproducer実行前に固定。初期A100/B50、nonce A0/B0、accepted_ids空、架空整数単位、総量150です。認可表はalice→A/bob→B。actorは信頼済synthetic fixtureで、認証・署名・鍵の検証を実装したとは呼びません。

単一プロセスが与えられた順に検査し、採用時だけ引落し/加算・送金元nonce＋1・txID追加を行います。拒否時は残高/両nonce/id一覧を全て保持します。検査順はknown actor→nonce型/非負→amount型/正値→account→未使用id→認可→期待nonce一致→残高。boolはPython intのsubclassでも明示拒否。条件が重なる場合はこの順の最初の理由を返します。検証対象は固定13条件で任意JSON/schemaの安全性保証ではありません。

| 条件 | 採否 | 最終 A/B/A nonce |
| --- | --- | --- |
| alice nonce0 amount10→別id nonce0 amount20 | ACCEPT→NONCE_CONFLICT | 90/60/1 |
| amount20→amount10の逆順 | ACCEPT→NONCE_CONFLICT | 80/70/1 |
| nonce無視の故障 | ACCEPT→BAD_ACCEPT | 70/80/2 |
| bobによるA引落し | UNAUTHORIZED | 100/50/0 |
| 認可を省くbalance-only故障 | BAD_ACCEPT | 90/60/1 |
| unknown actor / bool nonce / 不正amount | 各入力拒否 | 100/50/0 |
| amount101 / future nonce1 | 残高不足 / NONCE_CONFLICT | 100/50/0 |
| 採用済txIDをnonce1で再送 | ACCEPT→DUPLICATE_ID | 90/60/1 |

balance-only故障は認可guardだけを省き、型・id・nonce・残高は残します。nonce無視故障はnonce一致guardだけを省き、認可は残します。2故障を混ぜません。総量150は故障でも保存されるため正当性の証明ではありません。別txIDはnonce競合を回避せず、正しいnonceも同じ採用済idの再送を正当化しません。先着順による結果差は合成入力列の差で、分散consensus/fork/finalityを再現しません。

MIXED_DECISIONSは採用と拒否を含む列、ALL_REJECTEDは全拒否、BAD_ACCEPTEDは故障受入です。processing_started=trueはvalidatorが動いた意味で、送金採用とは別。各行acceptedとdecisionを読みます。実行障害EXECUTION_FAILUREはoracle未判定で、期待拒否の成功件数へ混ぜません。

## 再現と独立検査

~~~sh
python3 -B runner.py --record
python3 -B check.py
python3 -B route.py account-authorization-nonce-conflict
python3 -B route.py unsupported
~~~

--recordだけ新UTC folderを作り、既存原票を書き換えません。checker/routeはread-only、unsupportedはexit2。[oracle](oracle.py)はproducerの判定/遷移をimportせず、事前literal採否・全state順序表を使います。checkerはfixture・source SHA・UTC、各before/after・id一覧・認可/nonce観測と最終stateを照合。13条件17取引、通常採用4/故障採用2/期待拒否11（strictケースだけなら採用3/拒否11）。strict11case、故障2case。6mutantを拒否します。

[検証receipt](observations/verification.json)は実IAB全条件の答え、予想/条件reset、合成return/HTTP503失敗、実旧応答の遅着破棄、所有tab/server終了、read-only全file SHA/mtime照合へ接続。sandbox実bind errno1を保存し、同じlocalhost commandをhost permissionで実行しました。合成QA失敗はproducer実障害ではありません。captureはtool実表示のみ、保存ファイルなし。同一agent[module-local Skill](skills/atlas-account-authorization-nonce-conflict/SKILL.md) routingは独立Forward Evalではありません。

## 原典・nonceの境界・未教材

2026-10-06 JSTに[NIST IR8202 §3.2 transactions（冊子pp9–10 / PDF20–21）と§3.3 asymmetric-key cryptography（冊子pp11–12 / PDF22–23）](https://doi.org/10.6028/NIST.IR.8202)を確認。署名と鍵による取引検証の概観を、認証未実装との境界として参照します。歴史的文書のalgorithm例を現行実装推奨として転用しません。

同原典§3.1.1（冊子p9/PDF20）のcryptographic nonceはhash/PoW用途の説明です。本unitのaccountごとの期待整数nonce、拒否時不変、採用時＋1は独自規則で、この文書や特定chainへの準拠とは呼びません。例/実装/表は独自制作、第三者本文・図の転載なし。

未教材：署名/鍵/actor認証、実account chain/UTXO、mempool/nonce gap/replacement、同時実行/永続化/atomicity、node合意、fork/finality、network、Merkle、実資産、wallet、smart contract。他browser/学習者評価も未実証。次案は独立fixtureでB自身の送金とactor認証を分離、nonce gap/replacement方針の明文化、同時候補のatomic commit、署名fixtureの改変拒否を別unitで行う。全て未制作。Core/fullGate・commit/push・公開・install/設定/権限拡張・課金は対象外です。
