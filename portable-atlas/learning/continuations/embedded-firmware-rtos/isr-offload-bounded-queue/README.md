# ISR offloadと有界queue — 受入は処理完了か

固定event ID0/1/2がtick0/1/2に到着し、consumerがtick3以降に最大1件ずつ完了するPython標準ライブラリ教材。実IRQや実RTOSを呼ばない論理モデルです。

## 前提と読む順序

list、FIFO、JSON、整数tickが前提。

1. [元Subject](../../../subjects/embedded-firmware-rtos/README.md)のRMW・critical sectionとoffload候補を読む。
2. producer実行前に固定した[契約](EXPECTATIONS.md)と[36行のliteral tick表](oracle.json)を読み、drop/喪失と完了の2予想を立てる。
3. [UI](index.html)でcapacity2→capacity3→単一slot故障→empty/capacity0→拒否を実Pythonで比較。
4. [Zephyr一次資料と対応](SOURCES.md)、[実装](producer.py)、[独立検証](oracle.py)へ戻り、答えを開く。
5. [関連2server有界queue](../../performance-capacity-engineering/two-server-bounded-queue/README.md)のoffered/accepted/finished・producer待ちを比較する。両モデルの時刻位相は異なる。

## 実行と保存

このディレクトリで実行。追加依存・Docker不要。通常コマンドは保存しない。明示recordだけ新UTC/UUID原票を追加し、旧rawを保持。

```sh
python3 -B runner.py --case capacity2
python3 -B runner.py --case capacity3
python3 -B runner.py --case slot-overwrite
python3 -B runner.py --case capacity0
python3 -B runner.py --case event-id-bool  # 意図的拒否 exit2
python3 -B runner.py --record             # 明示保存だけ
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py offload
python3 -B server.py
```

serverが印字する動的127.0.0.1 URLを開く。終了は自分のserverへCtrl-C。[runner](runner.py)は18個の実子プロセスのUTC・exit/stdout/stderrを保存し、[current](evidence/current.json)からimmutable rawへ接続。[binding](evidence/binding.json)と[QA](evidence/ui-qa.json)でsource・保存資料・実IABを結ぶ。HTTPは同じproducer関数を呼ぶが子プロセスではない。

## 正常・故障・境界

|条件|到着/受入/drop/完了/受入後喪失|完了ID→tick|
|---|---|---|
|capacity2 reject-newest|3/2/1/2/0|0→3, 1→4。2を拒否|
|capacity3|3/3/0/3/0|0→3, 1→4, 2→5|
|単一slot上書き故障|3/3/0/1/2|2→3。0/1は受入後喪失|
|empty|0/0/0/0/0|なし、正常|
|capacity0|3/0/3/0/0|なし、正常|
|capacity1|3/1/2/1/0|0→3|
|11不正入力|未計算null|exit2、理由を比較|
|実RuntimeError注入|未計算null|exit1、正常答えなし|

capacityは待機queueのID数。tick末に到着/受入/drop/完了/lostを累積記録、queueのみ現在状態。各tickのconsumer処理完了は論理規則で物理処理時間ではない。ID/tick0..2、重複なし、tick昇順、厳密id/tick field、event0..3件、capacity0..3の整数のみ。bool・未知mode・slot capacity2以外は拒否。

## UIの比較と消去

両予想欄それぞれ成功→答えを開く→一欄変更で、新しい予想と他欄を保持し旧比較・raw・table・count・答え本文を消しdetailsを閉じる。条件resetは予想とJSONも消す。拒否は未計算と理由を比較、実Errorは正常答えなし。

「応答を保留して実行」は実HTTPを既に受信し、描画適用のみ保留する。「保留応答を受け取る」で条件/予想変更後の旧versionを破棄し最新比較を保つ。通信遅延を測定したとは呼ばない。sleepなし。

## 実務判断と未教材

到着3、受入3を完了3と読み替えない。満杯拒否と受入後のslot喪失を分け、drop0でもloss0とは限らない。capacity増加はこの有限burstを保持する結果で、無限到着の処理能力を示さない。

このSubjectのqueue/offload入口の一部だけ。次の実験はpriorityと長いconsumer、複数producerのmemory order/SMP、実機ISRのWCETとoverflow復旧。実IRQ・nested ISR・priority・memory ordering・SMP・WCET・deadline・Safety保証は未実証。

[有限Skill](skills/atlas-isr-offload-queue/SKILL.md)は既存runner/UI/checkerへ限定route。独立agent評価ではない。Core/fullGate/commit/push/公開/インストールはこの有限課題では未実行。Subject全体やAtlas全体の完了は主張しない。
