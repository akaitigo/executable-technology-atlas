# 未教材と次の実験

元[Messaging Subject 実験3](../../../subjects/messaging-event-driven-systems/README.md)から、有限backoff/DLQ/redrive/identityを追加。元Subject・Portalは変更しません。

|未実証の問い|次の有限実験（未実施）|一次資料locator|
|---|---|---|
|実DLX targetが利用不可なら何が残るか|専用broker環境で確認方式とqueue種別を固定しrepublish失敗を観測|[DLX Safety](https://www.rabbitmq.com/docs/dlx#safety)|
|並行redriveとmarker競合はどうなるか|専用2consumerで同ID/同payloadと変更payloadのtransaction競合を比較|[RabbitMQ Reliability](https://www.rabbitmq.com/docs/reliability)|
|DB外effectとID変更は業務重複を防ぐか|合成外部service/outboxでlogical business keyとtransport IDを分離して追試|[Publisher Confirms](https://www.rabbitmq.com/docs/confirms#publisher-confirms)|

実broker/耐久性/外部effect/ID変更での業務重複回避/実時間delay/並行処理は未実証。x-death header形式をSQLite履歴へ同一視しません。
