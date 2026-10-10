# 元coverage → 今回 → 残範囲

[元IoT](../../../subjects/iot-device-connectivity/README.md) README:58 data/durability。今回は合成reboot epochとseqのidentity、history/latest分離だけの有限実証。

| 未実証の問い | 次の有限実験案（未実行） | 背景原典 |
|---|---|---|
| epochを再起動・backup復元後も非再利用にできるか | 永続発行器へwrite失敗/復元故障を入れ独立token表を比較 | [MQTT5 §4.1.1](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html)（epochの規定ではない） |
| session/broker状態が失われたら何が再送されるか | 隔離brokerでsession expiry/ACK lossを検証 | [MQTT5 §4.1/§4.3](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html) |
| 認証、seq wrap、flash耐久性をどう扱うか | 合成credential、有限wrap policy、write cycle故障を別契約で検証 | [NIST IR8259A](https://csrc.nist.gov/pubs/ir/8259/a/final)（入口、今回未検証） |

[関連CAS](../../operational-data-stores/key-generation-cas/README.md)もgeneration非再利用を仮定する。どちらも分散発行器の保証ではない。
