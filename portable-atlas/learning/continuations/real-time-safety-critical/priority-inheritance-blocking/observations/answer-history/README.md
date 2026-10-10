# 優先度継承とロック待ち時間

前提は整数tick、実行可能（ready）とロック待ち（blocked）、排他所有、優先順位です。[元の期限・EDF教材](../../../subjects/real-time-safety-critical/README.md)の「blocking、priority inversion、PI」へ進む有限単元です。ここは固定優先度H>M>Lを使い、元教材のEDFへPIを追加したものではありません。

1. Lがロックを持つ間、Hを待たせてMが実行すると、Hの待ちが何tickになるか予想します。
2. このディレクトリで`python3 -B verify.py`を実行し、`python3 -B serve.py`の動的URLで[操作画面](index.html)を開きます。終了はCtrl-C。
3. PIあり／なしとHの絶対期限を選び、予想を比較します。tickを動かし、CPU、ロック所有者、ready／blocked、基本／実効優先度、期限を追います。
4. 正常な終了、期限超過、不正tickの拒否を区別し、原典・実装・rawへ戻って答えを説明します。予想変更は新しい値を保ち旧比較・答えを消去。条件変更は予想も消去。不正tickは既存対照を保持します。

## 先に固定する模型

架空の単一CPU、1ロックK、1tick単位、context switch等のoverhead0、各タスクは一度だけ到着・完了します。Lはt0到着・K取得・critical3tick、Hはt1到着・同Kのcritical1tick、Mはt1到着・ロックなし4tick。基本優先度はH=3、M=2、L=1（この模型では大きい値ほど高い）。L/Mの絶対期限8、Hの期限4が標準、期限2は短期限の対照です。deadlineはdispatch順に使いません。

境界では前tickの完了・解放→到着→優先順のロック試行／block→空いたロックの待ちタスク取得→基本優先度に戻してPI伝播→最高実効優先度をdispatch→区間[t,t+1)を1tick実行→t+1で完了解放、の順です。取得・待ち開始自体はCPU tickを消費しません。完了=期限なら期限内、期限到達時に未完了ならmissを保持します。t8は最終状態でCPU実行はありません。

| 条件 | 手書きCPU順（t0〜7） | L解放 / H待ち終了 | Hロック待ち | H完了 / 期限4 |
|---|---|---|---|---|
| PIなし | L M M M M L L H | t7 | t1〜7=6tick | t8 / miss、lateness4 |
| PIあり | L L L H M M M M | t3 | t1〜3=2tick | t4 / 期限ちょうど |

PIありではHがblockしたt1からLの実効優先度が3に上がり、Mの割込みを防いで残り2tickのcritical処理を進めます。解放後Lは基本優先度1へ戻ります。両条件ともL3/H1/M4、計8tickの仕事が完了し、PIは仕事を削りません。待ち時間はH自身の1tick実行を含まず、response timeは完了−到着なので7／3tickです。期限2ではPIありでもH完了4でmissします。

## 原典・独立照合・実務判断

[Linux公式 RT-mutex design / Priority Inheritance (PI)](https://docs.kernel.org/locking/rt-mutex-design.html#priority-inheritance-pi)では、高優先度の待ちタスクの優先度を所有者が継承し、解放後に継承を失う仕組みを読みます。原典のunbounded inversion説明はMが際限なく走る可能性を含みますが、この模型のMは4tickで有限です。このtraceを無限待ちの実証とは呼びません。

[事前fixture](fixture.json)と[手書きtimeline・所有表](hand-oracle.json)をproducerより先に固定。[Python event model](source.html?file=model.py)の結果を、producerをimportしない[独立oracle](source.html?file=oracle.py)で照合します。oracleは手書きCPU列のprefixから各タスクのservice量を数え、所有／blocked／優先度表を別に検査します。[checker](source.html?file=verify.py)と[実行raw](observations/attempt-01/raw.json)で条件・全境界状態・イベントを確認できます。

実務では、待ち時間を測る始点・終点、critical sectionの残量、dispatch順、期限境界を固定し、blocking・response time・期限超過を分けて保存します。PIがあるというだけで期限達成を判断せず、到着・実行量・ロック依存を含む解析が必要です。

関連する[2ロックのdeadlock／retry教材](../../formal-methods-verification/two-lock-deadlock-livelock/README.md)は所有と進行を検査します。今回の優先度逆転は循環待ちを作らず、2ロックのdeadlock freedomやretryの終了性をこのPI結果から推定できません。

## 検証範囲と次の学習

Python標準ライブラリのみ、Mac上の抽象模型です。4条件×9境界=36状態、事前手書き照合、入力拒否、誤証拠検出、UI状態保持を検査します。実OS/RT-mutex全仕様、複数ロック、PI chain、timeout、WCET、割込み、実機安全認証は未実証です。分野全体の完了ではありません。[出典locator](sources.json)、[未教材と次3実験](coverage.json)、[検証記録](VERIFICATION.md)、[限定Skill](skills/atlas-priority-inheritance-blocking/SKILL.md)を参照してください。

明示記録`python3 verify.py --record attempt-01`は未使用名限定。通常検証・route・UIは既存原票を読み、bytecodeや原票を書き換えません。`--seal-record`はrawを保持し現在sourceと後続QAを別時刻で束ねます。元Subject／他単元を変更しません。
