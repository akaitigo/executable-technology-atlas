# IoT Device Connectivity

2つの合成deviceの切断queue→再接続→順不同再送を実装した有限教材。[index.html](index.html) で予想→操作→connection diagram/queue/receiver比較→原典/実装→答えへ進む。実device・MQTT broker・firmware更新・物理通信は未実行。

## 学習の道筋

1. 前提: device ID、sequence、JSON記録、有限queue。接続状態とデータの新旧は別概念。
2. 主要概念: store-forward、bounded queue、overflow policy、重複識別、device別high water mark、最新状態と履歴の用途の差。
3. 今回の実装: [telemetry.json](telemetry.json) のa/b各seq1–4、[model.py](model.py) の共有queueとreceiver。最初のseq1はonline、seq2–4をoffline queueへ入れ、reconnectでdrainをforward/reverse順に1–3batch再送する。逆順は合成アプリ到着順。MQTT接続内のwire順序を逆転させる実装ではない。
4. 正常/境界/異常: FIFO正常、順不同、duplicate、capacity1/6、drop-oldest/reject-newest、不正sensor raw、未対応入力を比較する。
5. 実務判断: 最新状態を守るなら(device,seq)の重複排除に加えてdevice別単調性が必要。全測定履歴やevent-time集計が目的ならstaleを捨てる方針は不適切。容量・overflow・再送順序・受信側用途をセットで設計する。
6. 限界: 永続化、ACK、再起動epoch、sequence wrap、実校正、認証、実ネットワークは別問題。下のcoverageから次の問い/実験/公式原典へ進む。

## 実行

このディレクトリでPython標準ライブラリだけを使う。

```sh
python3 -B run.py --capacity 6 --policy drop-oldest --order reverse --copies 2 --sensor valid
python3 -B run.py --capacity 1 --policy reject-newest --order forward --copies 1
python3 -B run.py --sensor invalid-sensor
python3 -B check.py
python3 -B server.py
```

serverの表示する127.0.0.1の一時port URLを開く。終了はCtrl-C。専用UI/APIだけを配信し、親directoryを公開しない。通常 [check.py](check.py) はread-only、原票更新は `python3 -B check.py --record` を明示する。

capacityは整数1..6、copiesは整数1..3。policyはdrop-oldest/reject-newest、orderはforward/reverse、sensorはvalid/invalid-sensorのみ。無効なCLI入力はJSON rejectedとexit2、HTTP400、UIは前回結果を消して入力拒否。不正raw fixtureはa seq3を1001に置き換え、入力全体を落とさずそのrecordだけをqueueへ入れる前に拒否する。

## 仕組みと比較

| 検査 | 正常/境界 | 意図異常・判断 |
|---|---|---|
| queue容量 | 6でoffline全6record、1で1record | drop-oldestは末尾、新着拒否は先頭を保持。損失は復元しない |
| 再送順序 | forwardならdevice別seq上昇 | reverseでnaiveの最新はseq2へ回帰 |
| 重複 | copies1 | copies2/3でnaiveは同一recordを繰り返し採用 |
| device key | a1/b1は別record | seqだけのglobal keyはbを誤ってduplicate扱い |
| 単調性 | protectedの最新seqは下がらない | dedupだけでは初到着の古いseqを止められない |
| raw入力 | 無単位整数0..1000 | bool/float/範囲外は拒否。sensor校正や物理単位の正しさは未検証 |

protectedはまず(device,seq)のseenを確認し、既知ならduplicate。未知でもdeviceの現在seq以下ならstale。staleもseenへ記憶するため次のcopyはduplicate。採用時だけ最新値を更新する。naiveは全arrivalを採用する。receiverのfault-global-key/fault-no-monotonicはcheckerの意図故障比較だけに使い、UIの選択肢にしない。

デフォルトcapacity6/reverse/copies2は14arrival。protectedは4採用・6duplicate・4stale、最新a4/b4。naiveは14採用で最新a2/b2。capacity1/reject-newest/forward/copies1は3arrival、最新a2/b1で、bのoffline測定は失われる。logical stepは実時間ではない。sequenceはアプリ独自の1..99整数でMQTT packet identifierではない。同じkeyに異なるpayloadが来る競合は検査対象外。

## 独立oracleと証拠

[oracle.py](oracle.py) はmodelをimportせず、固定fixtureを別に定義。queueは有効offline記録のprefix/末尾slice、最新はdelivery prefixのdevice別最大seq、duplicateは同じkeyの過去出現で算出する。逐次queue/receiver実装とは異なる方法で全timelineを照合し、2つの手計算表も使う。

[evidence/run.json](evidence/run.json) に144組の入力、queue snapshots、損失、拒否、全delivery、receiver raw trace、独立期待、input/raw digest、実行時刻/環境を保存。[bindings](evidence/bindings.json) がsource/artifact digestと原典locatorを結ぶ。[UI QA](evidence/ui-qa.json) は実HTTP IABの操作・観測、captureの取得/保存可否、所有server/tabの終了を記録する。capture未保存を保存済みと扱わない。

[Skill](skills/atlas-iot-device-connectivity/SKILL.md) は既存runner/checker/UIへの限定route。[routing-smoke](evidence/routing-smoke.json) は主agentによる正常/未対応の実確認で、独立forwardAgentEvalではない。Core `atlas audit` / `npm run gate` は専用module scope外で未実行。全Subject完成は主張しない。Goalは作成しない。

## 未教材coverageと次の実験

| 概念・問い | 次の実験 | 公式locator |
|---|---|---|
| transport/session: QoS、keepalive、expiry、CoAP再送はどの保証を持つか | 合成ACK loss、session再開の比較 | [MQTT5 §3.1.2 / §4.3 / §4.6](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html)、[CoAP §4](https://www.rfc-editor.org/rfc/rfc7252.html) |
| data/durability: crash、epoch、seq wrap、dedup保持、event timeと履歴は | 合成crash/reboot、永続outbox、epoch keyと最新/履歴用途の比較 | [MQTT5 §4.1 Storing state](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html) |
| identity/security: device認証、credential更新、topic権限は | 合成credential期限とtopicの権限表比較 | [NIST IR8259A](https://csrc.nist.gov/pubs/ir/8259/a/final) |
| lifecycle/energy: provisioning、telemetry観測、電力制約、署名とrollbackは | 合成update中断、manifest検証とrollback比較 | [RFC9019 §3–4](https://www.rfc-editor.org/rfc/rfc9019.html) |

以上は未教材。実device、broker、radio、性能/電力計測、flash wear、実sensor校正、TLS、firmware更新、safety保証は含まない。queueがメモリー内なのでprocess終了で消える。dedup seenはこの有限実験中だけ保つ。現実には保持容量・有効期間・再起動後のidentityも設計する必要がある。

## 原典と実装の対応

- [OASIS MQTT5](https://docs.oasis-open.org/mqtt/mqtt/v5.0/os/mqtt-v5.0-os.html) §4.3 QoS / §4.6 Message ordering: 配送品質、重複、順序の原典。今回の再送とdedupはアプリ独自モデルであり、MQTTのQoSを実装・保証したものではない。
- [CoAP RFC7252](https://www.rfc-editor.org/rfc/rfc7252.html) §4.5: transport別の重複識別の次の原典。教材のkeyや保持期間とは異なる。
- [NIST IR8259A](https://csrc.nist.gov/pubs/ir/8259/a/final): device cybersecurity能力のcoverage。単なるtelemetry排除でセキュリティ完成を主張しない。
- [RFC9019](https://www.rfc-editor.org/rfc/rfc9019.html): firmware更新architecture。今回updateは実装しない。

公式ページを制作時に実取得確認。全文は複製しない。学習用の固定fixtureと方針を仕様の要求へ読み替えない。
