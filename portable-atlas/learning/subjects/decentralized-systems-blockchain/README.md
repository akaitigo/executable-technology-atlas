# 分散システム・blockchainを学ぶ入口

Macの標準Pythonだけで、task-ownedの架空append-only ledgerとbalance validatorを比較する有限1教材です。口座mock-a/mock-b、整数の架空単位のみ。consensus、live chain、実資産、金融助言、smart contractは扱いません。全97分野やこのSubject全体の完成を主張しません。

## 前提 → 主要概念と仕組み

JSON、SHA256、整数の足し引きを前提にします。初期残高はmock-a=100、mock-b=50、総量150。blockにはheight、previousHash、tx、claimed balances、hashを記録します。hash fieldを除くsorted-key compact JSON bytesにSHA256を適用し、次blockが前blockのhashを参照します。これは教材限定の形式で、RFC 8785/JCS準拠serializerではありません。

**hashの整合とtransactionの正当性は別の検査です。** naive chain_checkはhash/linkと固定genesisを照合します。完全validateはその後に、既知口座、正の整数amount、送金元残高、tx id未使用、厳密な残高遷移を検証します。総量が保存されるだけでは十分でなく、送金規則に従う配分も照合します。送信者署名や認可は未実装なので、完全検証という名称もこの教材の規則の範囲に限ります。

[model.py](model.py) の append は既存prefixを複製して候補blockを末尾へ追加します。validated_appendはprefixと候補の規則検査に通る場合だけ新ledgerを返します。既存blockを変更するAPIはありません。反例用candidateは不正候補や改変コピーを作ります。それらを受理済み履歴に混ぜません。単一writerが履歴全体とhashを作り直せるため、独立した改ざん防止や分散合意にはなりません。

## 今回の実装 → 正常・境界・意図異常

このディレクトリで実行します。追加依存・Docker・外部サービスは不要。`-B`はbytecode書き込みを抑止します。

```sh
python3 -B run.py --case normal --amount 10
python3 -B run.py --case all-spent
python3 -B run.py --case forged-balance
python3 -B run.py --case forged-conserving
python3 -B run.py --case tamper-hash
python3 -B run.py --case tamper-link
python3 -B run.py --case replay
python3 -B run.py --case negative
python3 -B run.py --case unknown-account
python3 -B check.py
python3 -B server.py
```

serverが印字する動的127.0.0.1 URLで [index.html](index.html) を開きます。止めるときは自分のserverへCtrl-C。[run.py](run.py) とHTTP [server.py](server.py) は同じ既存modelへrouteします。任意の実資産や実chainを取り込む入口はありません。

画面は **予想→操作→比較→原典/実装→答え** の順。固定ケースとamountを変えて、実block、previousHash/hash、tx、claimed balances、naive結果、完全検証結果、独立oracle、採用済みprefix残高、decision chainを比較します。amount入力は1–100。固定caseは定義された異常値/偽装値を優先します。画面は候補を再生成して表示し、受理ledgerのファイル更新はしません。

| case | naive / 完全検証の既定結果 | 理解する問い |
| --- | --- | --- |
| normal | accept / accept、90と60 | 正常送金で総量150を保つか？ |
| all-spent | accept / accept、0と150 | 100ちょうどは受理するか？ |
| zero / negative | accept / amount-rejected | hashが一致しても正値規則で拒否するか？ |
| overspend | accept / insufficient-balance | 残高100に対する101単位の送金を拒否するか？ |
| forged-balance | accept / balance-mismatch | hashを再計算した偽装で総量を増やせるか？ |
| forged-conserving | accept / balance-mismatch | 総量150でも配分が規則と違えば拒否するか？ |
| tamper-hash / tamper-link | hash-mismatchまたはlink-mismatch / 同じ拒否 | bytes改変と前hash参照を検査するか？ |
| replay | accept / replay | 同じtx idを再実行しないか？ |
| unknown-account | accept / unknown-account | 未知口座を拒否するか？ |
| boolean-amount | accept / input | Pythonのboolを整数として受理していないか？ |

forged-conservingの固定claimsは95/55なのでamount=5なら正しい配分となり受理されます。case名だけで拒否せず、実数値と遷移で判定することも確認します。

[oracle.py](oracle.py) はmodelをimportしない独立hash traversalとdebit/credit累積、12ケースの手計算表を使います。暗号primitiveには別のSHA実装を使わず、外部公開の `abc` 固定SHA256値を追加照合します。独立agent評価や形式的証明ではありません。[check.py](check.py) は12case×amount1–100の1200比較、入力拒否、prefix保存、受理append、意図的な残高/境界/replayの壊れたモデルを検査します。

通常checkerはread-only。原票更新は明示option `python3 -B check.py --record` だけ。[evidence/run.json](evidence/run.json) に実行時刻・環境・input・raw block・hash/link trace・残高decision chainとdigestを保存します。[evidence/accepted-ledger.json](evidence/accepted-ledger.json) は明示記録で作った、検証済み2送金を末尾へ加えた架空ledger。[evidence/bindings.json](evidence/bindings.json) はsource/artifact SHA256結合。[evidence/ui-qa.json](evidence/ui-qa.json) は実IAB QAとcaptureの保存可否を区別します。今回、実HTTP IABで14条件、title/fields、実block/hash図、原票開閉、答え、roadmapを確認しました。実full-page JPEG captureは取得・tool表示・目視確認済みですが、moduleへ未保存です。再描画ではありません。captureファイルの永続保存は未検証。自分のserver/tabは終了済み。

## 実務判断 → 限界

今回判断できるのは、hash/link検査だけでは業務規則を保証できないこと、初期状態と厳密な状態遷移の照合が必要なこと、replayのidと金額境界を検証する理由です。append-onlyのデータ構造、業務規則、認可、合意形成の条件を分けて説明できます。

残高が正しくても送信者が正当な権限を持つとは言えません。署名・鍵・nonce、node間競合、double spend、fork/finality、network partition、Byzantine耐性、保存rootの信頼、Merkle証明は未実装。これは単一プロセスのledgerで、分散システムや稼働blockchainの安全性を再現していません。実資産への送金、投資判断、smart contract実行は行いません。

## Subjectの主要未教材coverage → 次の4実験

| 未教材の概念・問い | 次の実験（未実装） | 公式locator |
| --- | --- | --- |
| P2P・複製・consensus・Byzantine障害・fork/finality：正しい履歴を誰が決めるか？ | 架空3nodeの遅延/分岐/投票を比較 | NIST IR 8202 consensus models |
| 署名・鍵・nonce・account/UTXO・double spend：誰が取引を承認できるか？ | 架空認可表と競合取引の採否を比較 | 同原典 transactions/asymmetric-key cryptography |
| Merkle証明・light client・canonicalization・検証コスト：全履歴なしで何を信頼できるか？ | 架空Merkle membershipと欠落/改変を比較 | 同原典 hashes、RFC 8785 |
| smart contract・決定的実行・data oracle・upgrade/governance：外部事実をどう扱うか？ | 架空状態機械の入力順/失敗/外部値差を比較 | 同原典 smart contracts/oracles |

実ネットワーク、実資産、wallet、DeFi、bridge、tokenomics、privacy、permissioned運用、consensus実装、smart contract実行は未教材/未検証。上記は次の候補であり今回着手しません。

## 原典へ戻る

- [NIST IR 8202](https://csrc.nist.gov/pubs/ir/8202/final)：hash・ledger・transactionとconsensusの概観。このモデルと分散blockchainの違い、主要未教材coverageへ結合。
- [FIPS 180-4](https://csrc.nist.gov/pubs/fips/180-4/upd1/final)：SHA256仕様。modelのhash計算の原典。
- [NIST SHA256 example](https://csrc.nist.gov/CSRC/media/Projects/Cryptographic-Standards-and-Guidelines/documents/examples/SHA256.pdf)：`abc` 固定値とoracle.ABC_SHA256の結合。
- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785)：JSON canonicalization。汎用serializerを学ぶ次の原典であり、本serializerの準拠を主張しない。

locator確認日：2026-10-05。source bindingは参照と実装/coverageの対応であり外部原典の完全ミラーではありません。

## Skillと検査範囲

[SKILL.md](skills/atlas-decentralized-systems-blockchain/SKILL.md) は既存runner/checker/UIに限定route。[evidence/routing-smoke.json](evidence/routing-smoke.json) は正常/未対応のmain-agent routing smokeで、独立forwardAgentEvalではありません。

module外の検査・編集は禁止です。repo全体の `npm run gate`、Core audit、repoctl admission verify は未実行。module成功をrepo全体gate成功、commit可能性、全Subject完成と扱いません。
