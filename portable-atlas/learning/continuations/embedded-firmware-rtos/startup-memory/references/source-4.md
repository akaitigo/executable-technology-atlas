# Embedded firmware・RTOSを学ぶ入口

Macの標準Pythonによる有限ISR/main loopモデルの1教材です。実firmware、実RTOS kernel、実device timing、Safety検証は行いません。Docker、追加依存、外部サービスは不要。全97分野やこのSubject全体の完成ではありません。

## 前提 → 主要概念と仕組み

変数、read/write、整数時間、割込みの基礎を前提にします。counter=0からmainとISRが各1回増分します。read-modify-writeをMR/MW、IR/IWの2段階に分け、read値をcontextごとのregisterへ保存します。mainがreadした後にISRが増分しても、mainが古い値を書き戻すとlost updateが起きます。

単一core・1 ISR・ISR run-to-completionを仮定します。各contextのread-before-writeを保つ全6順序を列挙し、そのうちISR途中にmainが動く3順序は未対応として拒否します。実行対象は次の3順序です。

| schedule | 要求順 | naive / critical counterの手計算 |
| --- | --- | --- |
| main-first | MR MW IR IW | 2 / 2 |
| preempt-main | MR IR IW MW | 1 / 2 |
| isr-first | IR IW MR MW | 2 / 2 |

critical方式はMR–MWを不可分な区間として扱い、途中のISR要求を保留してMW後にIR/IWを実行します。CPU atomic命令や実RTOS APIを呼ぶのではなく、IRQをmaskする単一coreのモデルです。scheduler lockとIRQ lockは別で、volatileだけでRMWがatomicになるとは扱いません。

**counterのoperation stepとIRQ latencyのtickは別の実験です。** counter traceのstepは操作番号で実時間ではありません。独立latencyモデルはcritical時にmask区間[0,hold)、ISR処理1tickを仮定し、IRQ arrivalから開始までのwait、完了までのresponseを計算します。naive時はmaskなし。arrival=holdなら待ち0。`response <= relative deadline` なら達成とします。実MCUの時間やWCETの測定値ではありません。

## 今回の実装 → 正常・境界・意図異常

このディレクトリで実行します。`-B`はbytecode書き込みを抑止します。

```sh
python3 -B run.py --schedule main-first --mode naive
python3 -B run.py --schedule preempt-main --mode naive
python3 -B run.py --schedule preempt-main --mode critical
python3 -B run.py --mode critical --hold 3 --arrival 1 --deadline 3
python3 -B run.py --mode critical --hold 4 --arrival 1 --deadline 3
python3 -B run.py --mode critical --hold 3 --arrival 3 --deadline 1
python3 -B run.py --schedule invalid-isr
python3 -B check.py
python3 -B server.py
```

最後のinvalid-isr実行は意図的な拒否で終了し、正常成功と混同しません。範囲はhold2–10、arrival0–12、deadline1–12。bool/非整数と未知mode/scheduleは拒否します。

serverが印字する動的127.0.0.1 URLで [index.html](index.html) を開きます。自分のserverへCtrl-Cで終了。[run.py](run.py) とHTTP [server.py](server.py) は既存 [model.py](model.py) へrouteします。任意の実deviceやfirmwareを取り込む入口はありません。

画面は **予想→操作→比較→原典/実装→答え** の順。scheduleと保護方式、hold、arrival、deadlineを操作し、naive/criticalの実counter step列、IRQ-deferred、実register trace、独立oracle、tick列、deadline結果を比較します。全原票を開くとinput、各比較のraw event traceとdigestが表示されます。画面操作は原票ファイルを書き換えません。

- 正常：main-first/isr-firstは両方式counter=2。
- 意図異常：preempt-mainのnaiveはcounter=1、criticalは2。
- deadline境界：critical hold3/arrival1/deadline3はresponse3で達成、hold4ではresponse4で未達。
- mask終了境界：hold3/arrival3はwait0、response1。
- 未対応：ISR途中にmainを挟むschedule、不正入力は拒否。

[oracle.py](oracle.py) はmodelをimportしません。全6順序と合法3順序の固定表、最後のwriterがread前に他のwriteを見たかという式、maskされたtick集合を用いて照合します。[check.py](check.py) は全6順序の分類、合法3×2方式のcounter、hold9×arrival13×deadline12×mode2の2808 latency比較、入力拒否、critical deferral・deadline比較・mask終了境界の壊れたモデル3件を検査します。独立agent評価や形式的証明ではありません。

通常checkerはread-only。原票更新は明示option `python3 -B check.py --record` だけ。[evidence/run.json](evidence/run.json) に実行時刻・環境・input/raw trace/digestを保存し、[evidence/bindings.json](evidence/bindings.json) でsource/artifactをSHA256結合します。[evidence/ui-qa.json](evidence/ui-qa.json) は実IAB QAとcapture保存可否を区別します。今回、実HTTP IABで10条件、title/fields、counter step/latency tick図、register原票開閉、答え、roadmapを確認しました。実full-page JPEG captureは取得・tool表示・目視確認済みですがmoduleへ未保存です。再描画ではありません。captureファイルの永続保存は未検証。自分のserver/tabは終了済み。初回default sandboxのbind EPERMは evidence/preview-initial-constraint.json に保存し、同sessionの通常承認審査後にpreviewを起動しました。設定変更や拒否後の別surface迂回はありません。[evidence/session-recovery.json](evidence/session-recovery.json) のモデル容量エラーはインフラ事象で、教材検査失敗/expected failureとは別です。

## 今回判断できること → 実務判断と限界

RMWが単一statementに見えても競合し得る理由、共有状態を保護する意味、保護区間を延ばすとIRQ responseが悪化する条件を説明できます。counterの正しさとdeadlineを両方評価し、critical section短縮やISR処理のthreadへのoffloadを次の判断候補にできます。

実機ではmask対象IRQ/優先度、nested ISR、SMP、atomic命令、memory order、cache/DMA、compiler、WCETとjitterを別に確認する必要があります。モデルのtickは物理時間ではなく、real-time性やSafety保証はできません。全6順序のうち3拒否はこの単一core ISR仮定によるもので、複数thread/SMPの一般並行性を否定するものではありません。

## Subjectの主要未教材coverage → 次の4実験

| 未教材の概念・問い | 次の実験（未実装） | 公式locator |
| --- | --- | --- |
| reset/startup・linker・memory map・HAL・GPIO/UART/DMA：どこで誰がhardwareを初期化するか？ | 架空memory mapとboot初期化順の依存を比較 | Zephyr Board Porting / Build |
| task priority・preemption・tick/timer・WCET・jitter・priority inversion：どのtaskがdeadlineを逃すか？ | 架空2task＋mutexのpriority inheritance有無を比較 | Zephyr Scheduling / Mutexes |
| queue/semaphore・ISR offload・buffer overflow・memory order・SMP：割込みをどう安全に渡すか？ | 架空producer/consumer queueで欠落/overflow/遅延を比較 | Zephyr Interrupts: Offloading ISR Work |
| watchdog・低消費電力・更新/rollback・fault recovery・debug/test・Safety：停止や失敗からどう復旧するか？ | 架空firmware更新状態機械で電断/rollback/watchdog条件を比較 | Zephyr Device Firmware Upgrade / Watchdog |

実cross compile/flash、実RTOS kernel、実device timing、cache/DMA coherence、nested IRQ/SMP、実消費電力、real-time/Safety保証は未教材・未検証。上記は次の候補で、今回着手しません。

## 原典へ戻る

- [Zephyr Interrupts: Preventing Interruptions](https://docs.zephyrproject.org/latest/kernel/services/interrupts.html#preventing-interruptions)：IRQ lockとlatencyの関係。モデル保護/待ちと限界へ結合。
- [Zephyr Scheduling](https://docs.zephyrproject.org/latest/kernel/services/scheduling/index.html)：ISRとthread schedulingの区別。合法schedule仮定と未教材task計画へ結合。
- [Zephyr Mutexes](https://docs.zephyrproject.org/latest/kernel/services/synchronization/mutexes.html)：次のpriority inversion/同期実験。
- [Zephyr Board Porting](https://docs.zephyrproject.org/latest/hardware/porting/board_porting.html) / [Build](https://docs.zephyrproject.org/latest/build/index.html)：未教材のboot/build/device導入。
- [Offloading ISR Work](https://docs.zephyrproject.org/latest/kernel/services/interrupts.html#offloading-isr-work)：次のqueue/offload実験。
- [Device Firmware Upgrade](https://docs.zephyrproject.org/latest/services/device_mgmt/dfu.html) / [Watchdog](https://docs.zephyrproject.org/latest/hardware/peripherals/watchdog.html)：更新/復旧の未教材coverage。

locator確認日：2026-10-05。FreeRTOS docsの2URLは取得不可だったため内容を根拠にせず、確認できたZephyr公式資料を採用しました。source bindingは参照とモデル/coverageの対応であり、特定Zephyr版やdeviceの検証証明ではありません。

## Skillと検査範囲

[SKILL.md](skills/atlas-embedded-firmware-rtos/SKILL.md) は既存runner/checker/UIへ限定route。[evidence/routing-smoke.json](evidence/routing-smoke.json) は正常/未対応要求のmain-agent routing smokeで、独立forwardAgentEvalではありません。

module外の検査・編集は禁止。repo全体の `npm run gate`、Core audit、repoctl admission verify は未実行。module成功をrepo全体gate成功、commit可能性、全Subject完成と扱いません。
