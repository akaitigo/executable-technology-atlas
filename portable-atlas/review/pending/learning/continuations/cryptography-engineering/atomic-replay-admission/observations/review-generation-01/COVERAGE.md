# 有限範囲の対応表

|問い|入力・証拠|確認方法|範囲外|
|---|---|---|---|
|分離で二重受入になるか|同じID・payload違い・境界ID/bytes、6順序|先行手表＋独立位置oracle＋全trace|無限要求列|
|atomicは同じIDを1件にするか|AB/BA、既登録、異なるID|独立oracle、seen/accept数|DB transactionや分散Lock|
|認証失敗で状態を変えないか|both invalid、mixed valid|実HMAC＋独立ipad/opad、state不変|鍵管理・鍵秘匿|
|実threadでも代表競合が起きるか|7fixture×2方式|check後BarrierとLock前Barrier、join/abort、生ログ|全scheduleの実機再現|
|制御失敗を隠さないか|意図的broken Barrier|両worker例外・accept0・全終了|OS故障や強制thread停止|
|壊した実装を検出するか|認証無視、always absent、remember欠落、replay計数、split再check、ID MAC欠落|変更したsourceを実行、独立oracleによるkill|包括的mutation score|
|教材として追えるか|fixture/順序、step/予測、比較、保存thread、source|実ブラウザDOM・実HTTP・inline screenshot|未保存画像のhash|

入力拒否23件: exactキー、要求2件、seen型/重複/上限/ID規則、ID型/長さ/文字、payload型/UTF8/bytes、tag型/hex長、schedule。invalid MACは形式違反と区別し、正常な拒否結果として表示します。

## 静的確認と未実測

Barrier位置、Lockのfinally release、期限付きjoin→abort→再joinはsourceの静的確認です。実測した制御失敗は、開始前にabortしたbroken Barrierで両workerがBrokenBarrierError、受入0、生存0となった1件だけです。Lock acquire timeout、片workerだけの例外、join期限到達は実測していません。これらを通過済caseへ数えません。
