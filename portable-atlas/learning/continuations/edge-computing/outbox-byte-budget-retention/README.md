# outboxのbyte予算と保持policy

元[Edge count/因果教材](../../../subjects/edge-computing/README.md)はevent数で容量を測りました。この続編はUTF-8 payloadのbyte数へ進み、専有SQLite DBへ実保存してclose後に別connectionで再読します。旧payload é=c3a9（2byte）、新abc=616263（3byte）、予算4です。全入力はsyntheticで、実edge/deviceやネットワークは使いません。

前提はUTF-8、queue保持、容量。画面で使用byte・保持数・変更write数を予想し、policy条件と新payloadを操作して実DB処理を行います。producer/別SQL read/独立算術、原典/source/raw、実結果から生成する答えへ進みます。

| 条件 | close後の保持hex | 使用byte | 新操作変更write数 |
| --- | --- | --- | --- |
| RejectNew＋abc | old:c3a9 | 2 | 0 |
| OverwriteOldest＋abc | new:616263 | 3 | 2（delete1＋insert1） |
| CharCountFault＋abc | old:c3a9, new:616263 | 5 | 1 |
| OverwriteOldest＋abcde | old:c3a9 | 2 | 0 |
| RejectNew＋é | old:c3a9, new:c3a9 | 4 | 1 |

文字数故障は1+3=4と判断して受け入れ、実byte2+3=5になります。BAD_ACCEPTEDは受入と予算超過が同時に起きた反例です。単体payloadが予算より大きければeviction前に拒否するので既存queueを削除しません。拒否理由FULLとSINGLE_PAYLOAD_EXCEEDS_BUDGET、入力拒否、EXECUTION_FAILUREの未判定は別扱いです。

[writer](calculate.py)は専有tmpDBのmessage(seq,id,payload BLOB)へseedをcommit後、新操作を処理してclose。[別readback](readback.py)はmode=roの新connectionでSELECT id,hex(payload),length(payload)を実行し、保持順序とusedbytesを確認します。producerのメモリ結果とは別の読取です。新操作write0はsqlite total_changesのseed後baselineとの差で、DB初期作成/seed保存を含めた総write0ではありません。payload使用byteはSQLite fileのdisk容量ではなくBLOB長の合計です。DB fileのSHA256をcleanup前に取得し、全専有tmpはfinally相当のTemporaryDirectory exitで除去します。

[事前literal hex/期待集合](hand-oracle.json)はproducer初回実行前に固定。[oracle](oracle.py)はproducer/SQLを共有せず、可変payloadをUnicode code pointからUTF-8 byteへ独立算術変換して保持集合を照合します。固定ケースはliteral表とも一致します。UI入力は最大16 UTF-16 code units、Python契約は最大16 code points（最大64byte）。一般Unicode入力や不正surrogateのproduction validatorではありません。10固定ケースに加え6可変payload原票を検査します。

可変反例：🍎=f09f8d8eは4byteでOverwriteOldest単体保持、ééはRejectNewで拒否、CharCountFaultではc3a9c3a9を追加して実6byte、éééは単体6byteなので旧queue保持で拒否。空payloadは拒否します。予測/payload変更は新値と他予測を保持し旧答え本文を空にして閉じ、trace/raw/比較を未実行へ戻します。条件変更は全予測unknownと既定payloadへ戻します。答えは実入力・実保持hexから生成します。

[Greengrass公式文書](https://docs.aws.amazon.com/greengrass/v2/developerguide/work-with-streams.html)のCreate message stream、Persistence、Strategy on full、TTLを原典文脈として確認しました。TTLは利用可能期間の保証で即時削除policyではありません。本unitは自作queue契約で、Greengrass SDK/API・内部容量計算・互換性は未実証。原典の保証をSQLite成功へ転写しません。

~~~sh
python3 -B check.py
python3 -B route.py outbox-byte-budget-retention
python3 -B route.py unsupported
~~~

最後はexit2で無変更。check/routeはread-onlyで、固定原票と可変原票を再読します。新しい証拠が必要な時だけpython3 -B runner.py --recordで新UTCディレクトリを作り、旧rawは変更しません。python3 -B server.pyは専有127.0.0.1動的portを表示し、そのprocessだけCtrl-Cで終了します。[Skill](skills/atlas-outbox-byte-budget-retention/SKILL.md)はこのunitの案内だけです。

[固定raw](observations/20261005T163153199786Z/raw.json)、[可変raw](observations/payload-qa.json)、[IAB](observations/iab.json)、[合成失敗](observations/failure-qa.json)、[実遅延応答の破棄](observations/held-qa.json)、[cleanup](observations/cleanup.json)、[receipt](observations/verification.json)。rawはUTC/Python/SQLite/OS、fixture、source hash、producer trace、別SQL read、DB SHA、cleanupを保持します。6mutantは文字数byte偽装、oversize既存消去、拒否write、exact拒否、未知policy許可、保持hex偽装を検出。captureは実tool表示確認のみ、保存fileなしです。合成return failure/HTTP503は実DB障害の証拠として扱いません。

未教材：複数旧messageのFIFO eviction、TTL/age、crash/power loss、lost ack/retry、実edge通信、暗号化、disk-full/WAL設定、実Greengrass。次候補はack前のprocess終了とreopen、複数messageでbyte保持の順序比較で、未制作です。close/reopen成功は停電耐久性ではありません。元Subject/旧freeze/Portal/Core/fullGate、OS/Docker設定、install/外部API/publication/commit/pushは対象外。Subject/Atlas全体完了は未主張です。
