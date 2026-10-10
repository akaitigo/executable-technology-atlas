# 手で定める継続期待

producerを作る前の手表です。各行は命令commit後、`tick=pc`。READはt4・t7・t9、STOREはt5・t8・t10です。

|tick|A|memory|counter|pending|そのtickの処理|
|---:|---:|---|---:|---|---|
|0|7|0,0,0,0|0|false|初期|
|1|7|0,0,0,0|1|false|NOP|
|2|7|0,0,0,0|2|false|NOP|
|3|7|0,0,0,0|0|true|発火、NOP|
|4|1|0,0,0,0|1|true|READ 1|
|5|1|1,0,0,0|2|true|STORE 0|
|6|1|1,0,0,0|0|false|発火してからACK|
|7|0|1,0,0,0|1|false|READ 0|
|8|0|1,0,0,0|2|false|STORE 1|
|9|1|1,0,0,0|0|true|発火、READ 1|
|10|1|1,0,1,0|1|true|STORE 2|

完全復元の各suffixはこの表のcut行から最後までです。cut0/2/3のREADは(4,1),(7,0),(9,1)、cut6のREADは(7,0),(9,1)。前のREADログを復元して数え直しません。

## deviceを落とした比較

cut2では、counter2を0へ戻します。その後のcounter列(t2..10)は0,1,2,0,1,2,0,1,2。発火がt5,t8へずれます。t4 READは0、t5 memory[0]へ0を保存。t6 ACK後のt7 READは0、t9 READは1なので、最終memoryは[0,0,1,0]です。

cut3ではcounterは元から0ですがpending=trueが消えます。counterと発火時刻は正常のまま、t4 READだけ0になります。t6の発火→ACKでpendingが正常側と再一致しても、t5に記録されたmemory[0]=0は残り、最終memoryは[0,0,1,0]です。

cut0とcut6ではdeviceは元から0,falseです。今回の欠落故障を補った値と同じなのでsuffix全値は一致します。失敗しなかった2例は全切断点の正しさを保証しません。

|条件|完全復元suffix|欠落版suffix|最初の状態相違tick|最初のREAD相違tick|
|---|---|---|---|---|
|initial|一致|一致|null|null|
|before-expiry|一致|不一致|2|4|
|pending-latched|一致|不一致|3|4|
|after-ack|一致|一致|null|null|

状態差には復元直後の境界を含みます。READ差は後で命令が返した値の差です。両者の時刻を混ぜません。全状態と各命令のtimer更新直後・READ/STORE/ACKはhand-oracle.jsonへ型付きで保存します。
