# encoded/decoded body budget — 同じabcでも3と23

Python実loopback HTTPと同origin実Browser ResourceTimingで、encoded body budgetを比較する有限教材。ASCIIabcはplain3 bytes、固定gzip23 bytes、decodeは3 bytes。gzipが常に小さいとは一般化しない。

## 前提と読む順番

HTTP Content-Encoding、JSON、整数bytes、fetch、ResourceTimingが前提。

1. [元Subject](../../../subjects/web-performance/README.md)のE2 network-loading/assets-budgetsを読む。DOM更新順やtimerとbodyサイズは別の問い。
2. producer採取前の[契約](EXPECTATIONS.md)と[独立literal hex/長さ/budget表](oracle.json)を読む。
3. [UI](index.html)で2予想→実fetch→encodedBodySize/decodedBodySize→budget判定を比較。
4. [一次資料](SOURCES.md)・[配信](server.py)・[Python判定](producer.py)・[独立HTTP照合](oracle.py)・実rawへ戻り、答えを開く。

## 正常と故障の固定表

|入力|実encoded/decoded|判定に使用|結果|
|---|---|---|---|
|plain budget8 encoded|3/3|3|受入|
|gzip budget8 encoded|23/3|23|拒否|
|gzip budget8 decoded流用故障|23/3|3|誤受入|
|gzip budget23 / budget22|23/3|23|受入 / 拒否|
|plain budget3 / budget2|3/3|3|受入 / 拒否|
|gzip budget3 decoded流用故障|23/3|3|誤受入|
|plain budget0|3/3|3|拒否|
|5不正入力|未計算|なし|INPUT_REFUSED|
|注入timing lookup欠測|表示未計算|なし|UNSUPPORTED_TIMING|
|実HTTP500|判定未計算|なし|EXECUTION_FAILURE|

budget0..23整数、bool不可、encoding plain/gzip、policy encoded/decoded-fault、variant normal/timing-missing/http-failure。JSON上書きはencoding/budget/policy/variantの4key厳密一致。現inputと実測値から答えを作る。故障policyでもbudget23なら正常encoded比較と同じ受入で、必ず誤受入とは呼ばない。

## 実計測と実行

このdirectoryで、自分のserverが印字する動的portだけを使う。

```sh
python3 -B server.py
python3 -B runner.py --case gzip8 --port OWN_PORT
python3 -B runner.py --record --port OWN_PORT  # 明示保存だけ
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py body-budget
```

OWN_PORTは印字された整数に置換。実行後自分のserverへCtrl-C。追加install・Docker・外部service・設定変更なし。runnerにportなしならUNSUPPORTED_LIVE_PORT/exit3で、測定したとは扱わない。通常runnerのliveはread-only、serverは自身のmemory receiptだけ保持する。

Python http.clientは生response bytesとheaderを読む。独立oracleが固定hex/23bytesとgzip.decompressのabc/3を照合。Browserは実fetch arrayBufferのdecode済bytes、実ResourceTiming entry、同request IDのserver receipt（実body hex/hash/write bytes）を結合する。Content-LengthをResourceTimingの値として代入しない。[保存current](evidence/current.json)・[binding](evidence/binding.json)・[実IAB QA](evidence/ui-qa.json)・[検証](evidence/verification.json)へ結合。

固定16条件を実子processで採取。PythonはResourceTimingを持たないため、timing-missing条件は生HTTPを採取しBROWSER_REQUIRED/exit3。Browser欠測注入は実fetch後のentry lookupを欠測扱いにする対照で、観測できたentryも原票へ残す。Browser実装本来の欠測を測定したとは呼ばない。HTTP500は実serverから受信する故障。entry deliveryの最大1500ms待ちは欠測検出用timeoutで、ネットワーク遅延のモデルではない。

原票は明示recordのみ新UTC/UUID名へ追加、旧raw保持。予期しないHTTP/child failureをcurrentへ昇格しない。checker/routeは保存rawのread-only照合でHTTP serverやBrowserを起動しない。

## UIと実務判断

全3入力は成功→開いた答え→一欄だけ変更で、新値/他欄を保持し旧測定・raw・本文を空にして答えを閉じる。条件resetは予想/JSONも消す。拒否・欠測・失敗は正常答えなし。受信済結果の描画保留で旧version破棄を比較し、通信遅延測定とは呼ばない。

encoded budgetにはencoded値を使う。decode済arrayBufferが3 bytesでもgzip bodyは23 bytes。受入/拒否の境界と入力のbudgetをそろえる。今回の小bodyではgzip overheadのため大きくなるだけで、一般の圧縮効果ではない。

## 未教材coverage

E2のbody-size入口だけを扱う。次の未実施実験は①実画像/font/JSの品質とbudget、②cache/再検証とcross-origin制限、③別browser/deviceの同一body追試。wire総bytes、latency、HTTP2/3・TLS、cache/CDN、圧縮率分布、WebVitals/RUM全般は未実証。

[有限Skill](skills/atlas-body-size-budget/SKILL.md)は既存HTTP runner/UI/checkerへ限定route。global install/独立agent evalではない。元Subject/共有Portal/旧教材を変更しない。Core/fullGate/commit/push/公開は有限課題では未実行。Subject/Atlas全体の完成ではない。
