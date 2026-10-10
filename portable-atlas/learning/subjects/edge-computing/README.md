# Edge Computing — 切断中の変更を、再接続でどう合わせる？

この有限1教材は、標準ライブラリによる **2 node の offline outbox sync model**。切断中のローカル更新、再接続、因果 version の比較、競合保持、buffer 上限と duplicate の境界を実行する。実 edge hardware、実ネットワーク、実 latency、CouchDB / Dynamo / Greengrass / MEC は未実行。Linux GUIを実行した教材でもない。この Subject 全体や Atlas 全分野の完成ではない。

[学習UI](index.html)は **予想→操作→保存実測比較→原典/実装→答え** の道筋。ボタンは保存した model execution の選択表示で、model の再実行や外部接続をしない。

## 前提 → 主要概念 / 仕組み

Python の list/dict と順序付き操作列、整数比較が前提。distributed system の知識がなくても次の具体例から読める。

- **配置（placement）**：edge は切断中もローカル更新を受け入れ、outbox に相手へ渡す event を保持する。central は接続中だけ更新を受け入れる。このモデルの「central」は配置ポリシーであり、実行 node は A/B の2つだけ。第3の cloud serverを起動しない。
- **因果（version）**：A は `[A counter, B counter]` の A 成分、B は B 成分を local editごとに1増やす。受信で各成分のmaxを取り、次のeditは観測した文脈を含む。全成分以上で少なくとも1成分大きいversionは古いversionを置換する。比較不能なvectorは同時更新なので両方のheadを保持する。logical clockの出発点は [Lamport (1978)](https://www.microsoft.com/en-us/research/publication/time-clocks-ordering-events-distributed-system/)、version vectorによる比較は [Dynamo §4.4 Data Versioning](https://www.amazon.science/publications/dynamo-amazons-highly-available-key-value-store)。Lamport scalar clock とこの2成分vectorを混同しない。
- **wall-clock**：観測時刻が大きいeventを1つだけheadにする比較版。時計が後戻りすると、因果的に後の更新を選べない。収束しても業務的に正しいとは限らない。
- **outbox / ack**：A1/A2はBへ、B1はAへ渡す。相手に適用またはexact duplicateと認められた後に元のoutboxから除去。切断中deliverは適用せず保持する。seenはIDとcanonical envelopeのSHA-256を記録。同じIDで異なるpayloadは競合として停止・保持する。
- **buffer limit**：本教材はevent個数で上限を測り、新規writeを拒否する方式。拒否はvalue/version/outboxを変えない。bytes/TTL/evictionやdisk durabilityはモデル化していない。

独立した更新を同期した後も競合を見える形にするという接点は [CouchDB conflict model §2.3.1/§2.3.3](https://docs.couchdb.org/en/stable/replication/conflicts.html)。ただしCouchDBのrevision treeを実装したわけではない。

## 今回実装：正常 / 境界 / 意図異常

共通offline入力：disconnect → Aが20をwall_ms100で保存（A1 `[1,0]`）→ Aが21をwall_ms90で保存（A2 `[2,0]`）→ Bが30をwall_ms80で保存（B1 `[0,1]`）→ reconnect → 両方向deliver。

A1→A2は明らかに後のlocal editだがwall-clockが100→90へ後戻りする。logicalはA2を保持し、同時更新B1も隠さない。wall-clock版は20だけをheadに残し、21と30はheadから失われる。`events/seen`の検証履歴は残るので、「全byteが消失した」とは主張しない。

| 条件 | 配送順の数 | 両nodeの最終head/value | 境界 / 判断 |
|---|---:|---|---|
| connected | 1 | B1:21 | BはA1受信後に編集。B1 `[1,1]` がA1を置換 |
| offline-logical | 6 | A2:21 と B1:30 | 因果後継と同時更新を全配送順で保持 |
| offline-wallclock | 6 | A1:20 | 時計後戻りで後のlocal value21を選べない。収束だけでは十分でない |
| buffer-one | 2 | A1:20 と B1:30 | A2をbuffer満杯で拒否、counterは1のまま |
| duplicates | 12 | A2:21 と B1:30 | A2を二重deliverしても状態不変。unique scheduleは4!/2! |
| conflicting-duplicate | 6 | A2:21 と B1:30 | 全original配送後にA1をvalue99に改変し再送、同ID別payloadを拒否 |
| invalid-value | 1 | empty | boolと101（上限100超）を拒否、version/outbox不変 |
| invalid-limit-zero / bool | 各1 | empty | limit0/trueをconfigで拒否し操作列を実行しない |
| empty | 1 | empty | 切断→再接続のみ、eventなし |
| central-offline | 1 | empty | offlineの3editを拒否、outboxを作らない |
| central-connected | 1 | B1:21 | connectedと同じvalue、配置costの仮定だけ違う |
| zero-value | 1 | A1:0 | value0は有効。offline sendはoutboxを保持し、reconnectで適用 |

13条件、40 unique delivery sequences。対象の3packet（duplicateでは4packet）の全順列を列挙するという限定的な「全sequence」で、任意の長さ・node数・障害列を網羅しない。checkerはmodel/runnerをimportせずliteralのevent/value/version/count/costと独立のschedule分母を照合。rawの切断前後の配置、outbox、拒否/duplicate時のstate不変も照合する。

### placement / latency のモデル入力とraw

`input.json.config.cost_model` の仮定は edge edit 2ms、remote RTT 80ms、remote compute 5ms。deliverは85ms。実行でsleepしない。rawの `at` はこのMacでmodelを実行した実UTC時刻、`modeled_ms` は計算した仮定値で、二つは別。

| 入力 | local edit cost | sync cost | 直列加算model cost |
|---|---:|---:|---:|
| connected edge（2edit+2deliver） | 4ms | 170ms | 174ms |
| central-connected（2edit+2deliver） | 170ms | 170ms | 340ms |
| offline-logical（3edit+3deliver） | 6ms | 255ms | 261ms |
| central-offline | 3拒否 | なし | 0ms（成功応答の速さではない） |

これは架空のcost modelの直列総和。response time、実RTT、平均/p95/p99、throughput、実際にedgeが何倍速いかの測定ではない。拒否/切断をcost0として成功と比較しない。UIの各raw行にplacementとonline/outbox/state、costを表示する。

### このMacで再現

Python 3.9以降の既存標準ライブラリのみ。Docker、外部service、new dependency、global installなし。

```sh
# このREADMEのあるディレクトリで実行
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
PYTHONDONTWRITEBYTECODE=1 python3 quick_validate.py
# 明示更新のみ: 新runを作り、oracle成功時だけUI pointerを更新
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record
# 表示された動的portをIABで開く。owned serverはCtrl-Cで終了
python3 -u -m http.server 0 --bind 127.0.0.1
```

[model](model.py)・[runner](runner.py)・[read-only checker](checker.py)・[原票pointer](observation-data.js)・[一次資料 binding](sources.json)・[限定Skill](skills/atlas-edge-computing/SKILL.md)。通常checkerは保存JSONを読むだけ。runner無optionは書かず終了。明示 `--record` だけが新原票とpointerを作る。古いrunを消さない。

各runの `run.json` に実UTC時刻/環境/source digest、caseの `input.json` に配置/clock policy/buffer/cost仮定/操作入力、各 `sequence-NN.json` に配送順・全operation・全raw snapshot・最終結果、`oracle-report.json` と `oracle-command.json` に独立比較、`artifact-index.json` にinput/raw/source/result artifact digestを保存。index自体は自己参照のため分母外。ハッシュはbindingを確認し、因果や業務正当性そのものを証明しない。

## 実務判断

今回から判断できること：切断中の書込みを受け入れるなら、同期までの鮮度と競合をUI/契約に出す必要がある。wall-clockで1winnerを決める設計は時計後戻りで因果後継を失い得る。vectorで競合を保持しても、21と30のどちらを業務値にするかは未決で、人/業務ルールの解決が必要。IDだけで重複排除せずpayload契約も検査する。buffer満杯時に拒否するならwrite受入を先に確定しない。local latency改善と全nodeの状態一致は別の判断軸。

実設計へ進む前に、offline受入期間、容量/保持、ID寿命、node再作成時のepoch、conflict解決、sync ackの耐久境界を書き出す。保持・buffer policyの公式出発点は [Greengrass Create message stream](https://docs.aws.amazon.com/greengrass/v2/developerguide/work-with-streams.html)。今回AWS APIは呼んでいない。

## 限界 / Subject主要未教材coverage / 次の実験

このSubjectを知るための次の道筋を4実験へまとめる。いずれも提案・未実行で、自動開始しない。

| 次の実験 | 主要概念と問い | 小さいinput・観測・比較 | 公式locator |
|---|---|---|---|
| E1: 配置と実測 | edge/fog/cloud、MEC、offloading、data locality、帯域/圧縮、cache freshness、mobility。遅延予算をどこで消費する？ | 許可済み2端末で同じ小payload/推論をlocal/remoteへ配置、RTT/compute/queue/転送byteを分けてp50/p95を採取。切断時のstale readとenergy/熱/resource制約も別観測 | [NIST SP500-325 / Fog nodes, deployment/service models](https://csrc.nist.gov/pubs/sp/500/325/final)・[ETSI MEC / Architecture and service APIs](https://www.etsi.org/technical-groups/mec/) |
| E2: 永続outboxと障害復旧 | durable queue、disk/TTL/bytes上限、backpressure、store-and-forward、ack/retry、power loss。rebootしても受入済みwriteを保持できる？ | 合成100eventを保存→ack直前process終了→再起動、bytes上限/TTL/RejectNewData/OverwriteOldestDataを比較。受入receipt、disk原票、duplicate、欠落、queue age/lagを照合 | [Greengrass / Create message stream, Append message, Persistence/TTL/Strategy on full](https://docs.aws.amazon.com/greengrass/v2/developerguide/work-with-streams.html)・[Manage data streams / intermittent connectivity](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-data-streams.html) |
| E3: 競合解決とmembership | CRDT、multi-value register、delete/tombstone、3+nodes、anti-entropy、vector pruning、epoch、causal context、business merge。node再作成で同じIDを再利用したら？ | 3nodesでoffline update/delete、1node再作成、duplicate/epoch conflictを混ぜ全小scheduleを検算。因果履歴保持とmax/min/unionなど業務mergeを比較し、消去を欠落扱いしない | [Dynamo §4.4 Data Versioning](https://www.amazon.science/publications/dynamo-amazons-highly-available-key-value-store)・[CouchDB §2.3.3 Revision tree / Working with conflicting documents](https://docs.couchdb.org/en/stable/replication/conflicts.html) |
| E4: fleetと信頼境界 | device identity、least privilege、encrypted storage/transport、OTA rollback、remote observability、configuration/version skew、safety/control deadline、service discovery。古いdeviceを再接続してよいか？ | 許可済みtest device2台で署名/version/identity不一致を拒否、更新失敗→rollback。sync lag、conflict数、disk使用、deadline missを記録しhealthと業務成功を分ける。MEC serviceの配置/移動とdevice権限を別テスト | [Greengrass / Data security](https://docs.aws.amazon.com/greengrass/v2/developerguide/manage-data-streams.html)・[ETSI MEC / Technical Specifications](https://www.etsi.org/technical-groups/mec/)・[NIST Fog conceptual model](https://csrc.nist.gov/pubs/sp/500/325/final) |

今回のmodelはin-memoryで、outbox persistence、node crash/reboot、lost ack、loss/retry/timeouts、実routing、security/OTA、real-time制御、resource/energy/thermal、外部sink等は実行していない。buffer count limitとbool/value拒否は指定入力の境界だけで、任意malformed inputに対するproduction validatorではない。

## 原典 → 答え

[source locator](sources.json)の `binding/status` から今回の簡略modelとの接点と未実行を読む。旧AWS locatorの取得エラーとETSI redirectも記録した。原典の保証をmodel成功へ転写しない。

今回の答え：**localに受け入れた変更はoutboxに保ち、因果的な後継を更新し、同時更新を隠さず、容量と重複の契約を明示する。** 2nodeの収束はedgeシステム完成を意味しない。[実IAB QA / capture / owned cleanup](qa/README.md)は実験原票と別の証拠。Core/Graph/Portal/harness、commit/push/公開、Goalは今回対象外。
