# priorityと長いconsumerでoverflowを比べる

[前のISR offload queue](../../embedded-firmware-rtos/isr-offload-bounded-queue/README.md)の次案「priorityと長いconsumer」だけを進める有限続編。既存教材は変更しない。Mac Python stdlibの単一consumer模型で、実RTOSを起動しない。

前提は整数tick・待機queue・priority・処理区間。予想→条件→実Python処理→service図/全tick trace→一次資料/source/raw→実入力の答え。capacity2、A処理4、同着B/C、続くD/Eでは受入ABC/dropDE。priorityはA,C,B、FIFOはA,B,Cで完了。Aを6に延ばすとhorizon8で実完了A,Cの2件、Bは処理中。受入3は完了3ではない。

[契約と手表](EXPECTATIONS.md)をproducerより先に固定。各tickは完了→同着を入力順に受入/drop→idleなら選択。capacityは待機だけ。priorityは大きい値が先、同priorityは受入順、実行中はpreemptionなし。完了直後でも待機が満杯なら、dispatch前の到着をdropする契約。RTOSの標準動作と呼ばない。[固定literal](oracle.json)のinterval集合から全tickの状態を展開し、[独立oracle](oracle.py)のevent-driven計算と[model](model.py)を比較する。

このdirectoryで `python3 -B server.py` を実行し、表示された専用127.0.0.1 URLを開く。各比較は実model子processと独立oracle子processを実行し、同request IDのmemory receiptも照合する。UIは合成時間をsleepで再現せず、戻った実traceからSVGを作る。専用server終了はCtrl-C。

条件JSONは全置換。exact capacity/horizon/policy/report/events、capacity0..3、horizon0..12、events0..6、id A..F重複なし、到着昇順、priority0..3、service1..6、整数はbool拒否。例はfixture.json。編集後の答えは入力ID・counts・start/end/wait/responseから構築する。未完了response・未開始waitはnull/未観測。accept-faultは受入IDを完了IDと誤報する対照で、実state/完了とは分離する。

全3入力の変更で旧結果/図/trace/raw/答え本文を消し閉じ、新予想・他欄を保持。条件変更は予想/JSONを初期化。実HTTP受信済み結果を保留し、変更後の旧versionを受け取っても最新結果を上書きしない。拒否・実RuntimeError・注入HTTP503に正常答えを出さない。503は自然ネットワーク障害の実証ではない。

~~~sh
python3 -B runner.py
python3 -B runner.py priority-overflow
python3 -B runner.py --record
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py priority
~~~

通常コマンドはread-only。recordだけ新UTC/UUID rawとcurrent pointerを保存し、旧原票は保持。モデルは純粋な有限整数計算でtmp fileを作らず、HTTP serverはmemory receiptのみ。記録は[evidence/current.json](evidence/current.json)、実IAB証拠は[evidence/browser.json](evidence/browser.json)、[検証結果](evidence/verification.json)。[一次資料](SOURCES.md)、[有限Skill](skills/atlas-priority-consumer/SKILL.md)。

未教材：実IRQ/RTOS/MCU、WCET/jitter/実時間、deadline/Safety保証、複数consumer/SMP/memory order、priority inversion/inheritance、preemption・外部副作用、無限到着とfairness、overflow復旧。次は有限mutexのpriority inversionとinheritance、別実機のIRQ→thread計測。いずれも未実行。Core/fullGate/install/公開/commit/pushを実行せず、Subject/Atlas全体の完成は主張しない。
