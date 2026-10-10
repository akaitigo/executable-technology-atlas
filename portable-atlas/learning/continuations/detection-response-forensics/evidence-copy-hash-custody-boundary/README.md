# 実コピーhashと引渡し台帳の境界

元[Detection / Response / Forensics](../../../subjects/detection-response-forensics/README.md)の最終未教材項目へ進む有限教材です。公開の架空ASCIIをMac標準Pythonで新しい所有tmp directoryへ書き、`shutil.copyfile`で複製し、実file bytesのSHA256を原本/複製前/改変後で比較します。実ログ・disk・device・任意user pathの入口はありません。

## コピーのintegrityと台帳を分ける

同bytesなら`integrity-match`、コピーの先頭1byteだけ変更すると`mismatch`です。原本を再読して保持を確認します。別に、evidenceID/from/to/seq/recordedHashの有限handoff台帳を照合します。actor未承認、seq欠落、別ID、hash記録相違、引渡し連続性切断は台帳整合拒否です。故障版はhash一致だけで「由来も承認済」と誤passします。同hash・未承認actorの反例で、bytesの比較から由来の承認へ飛躍できないことを観測します。

|固定入力|integrity|有限台帳|正常 / 故障|
|---|---|---|---|
|同bytes・整合台帳|match|整合|有限pass / 由来承認と誤主張|
|コピー先頭1byte変更|mismatch|原本hash記録は整合|mismatch / mismatch|
|未承認actor、seq 2欠落、別ID|match|拒否|ledger_refusal / 由来承認と誤pass|
|recordedHash相違、from連続性切断|match|拒否|ledger_refusal / 由来承認と誤pass|
|abc / bbc対照|一致 / 1byte相違|整合|独立literal hash比較|
|非ASCII、bool seq、seq field欠落、path field、壊れたJSON|未コピー|未判定|入力契約拒否、正常答えなし|

## 原典と独自契約

[NIST SP 800-86出版ページ](https://csrc.nist.gov/pubs/sp/800/86/final)と[原典PDF](https://nvlpubs.nist.gov/nistpubs/legacy/sp/nistspecialpublication800-86.pdf)を2026-10-06 JSTに確認しました。§3.1.2（文書3-4 / PDF p.28）は、取得後の原本/コピーdigest比較と、誰が何をいつ扱ったかの記録を説明します。§4.2.2（4-7〜4-8 / PDF p.39〜40）は原本保全とfile integrityの範囲です。

この模型はNISTのchain of custody手続を再現しません。時間、実保管、署名、本人確認、原本媒体のwrite-blocker、法的評価がありません。SHA256一致と出所・真正性・法的chain of custodyは別です。承認actorは固定の架空ラベルcollector/custodian/analystだけで、ID認証ではありません。法的証拠能力や実収集の可否を判断しません。

入力は[contracts](contracts.json)のexact fieldsだけ。payloadは1..256 ASCII byte（printable/LF/TAB/CR）、evidenceIDはE-数字3桁、mutateはbool。handoffは1..4件、seqはexact int 1..99（bool不可）、recordedHashはlowercase hex64桁。台帳は入力順にseq1から連続、最初from collector、fromは前のtoと連結、各ID/原本hash一致、actorは許可ラベル、最終to analystを照合します。ルールは本教材独自です。schema違反はコピー前の入力拒否、整合違反はコピー後の台帳拒否、OS/通信失敗は実行失敗として分けます。

[expected-table.json](expected-table.json)はproducerより先に固定したliteral bytes/hash/台帳期待です。hashは独立した既存`shasum -a 256`で事前確認し、oracleはhashlib/evaluatorをimportしません。元payloadのSHA256は`c3e3ac285dc508cbcc0eb503af054bd89c5c9c363ab482f99b3a6438c1860430`、先頭P→Qは`2e1bb914a2a8837fd44fe174a6736f48bf1659b32c97514214ec2c82125f7f74`です。

## 実行・UI・原票

```sh
python3 -B checker.py
python3 -B runner.py
python3 -B runner.py --record
python3 -B server.py --record
python3 -B qa/check-ui.py
```

通常checker/runner/QAは全unitファイルのSHA256/mtimeを維持します。各実コピーは所有TemporaryDirectoryをfinally相当のcontext exitで除去し、結果にcleanupを記録します。明示recordだけfresh UTC IDの不変原票を新規保存し、旧失敗も残します。source/hash/stdin/stdout/exitと実resultを結合します。observation-data.jsは現在原票の索引です。serverは所有loopback動的portのunit内配信だけです。

UIは予想→操作→正常/故障→原典/source/raw→実入力の答え。textareaの合成文字列・handoff条件を毎回実Python subprocessへ通し、返ったbytes/hash/ledger errors/cleanupから答えを作ります。全例/予想/JSON変更と比較開始では答え本文・trace・結果・rawリンクを空にし、detailsを閉じ、新値を保持します。revisionの古い応答は破棄。入力拒否や実行/通信失敗に正常答えを出しません。600ms preview遅延はstale QA専用です。

[実IAB QA](qa/README.md)へreset/編集/拒否/stale/failure/capture/cleanupを保存します。IAB別tabでJSON/Markdown表示がblockedなら制限を残し、回避しません。元Subjectはunit-only serverではなくfilesystemで検証します。

## 未検証とfreeze

実forensic収集、時刻の信用、本人認証、署名、原本の真正性、物理custody、write-blocker、実ログ、device imaging、法的評価、完全なNIST準拠は未検証。Core/Portal/他unitは変更せず、全体audit/gateは中央統合範囲です。有限unitのみをfreezeします。
