# deadline missとmodel flagを有限EDFで比べる

2 periodic taskのrelease/deadline/finishを、Python標準ライブラリのdeterministic discrete-event simulatorで計算する1教材です。負荷0.75、1.00、1.25を比較し、miss後に表示用safe-state flagをlatchedにします。flagは実安全装置ではなく、実CPU停止・機器出力の安全化は行いません。

## 起動とread-only検査

このmoduleディレクトリで実行します。今回の環境はCPython 3.9.6 / Darwin arm64、追加依存なし。Python 3.9は保守終了済みで、保守中Pythonでの追試は未実施です。

```sh
python3 -B test_runner.py
python3 -B runner.py --case normal --horizon 12
python3 -B runner.py --case boundary --horizon 12
python3 -B runner.py --case overload --horizon 12
python3 -B serve.py
```

サーバーはport0でOSが未使用loopback portを選び、実URLをstdoutへ出します。別ターミナルでサーバーを保持し、そのURLを開きます。終了はCtrl-C。必要なら`--port N`を指定できますが、他担当のlistenerは停止しません。localhostはUI→Python計算にのみ使います。

通常runner/checkerはstdout/stderrのみ、bytecode・原票を更新しません。原票保存が必要な場合だけ明示optionを使います。

```sh
python3 -B runner.py --case overload --horizon 12 --record
python3 -B test_runner.py --record
```

保存はUUID名`observations/run-*/`、`checks-*/`へ追記、UIの明示buttonは`ui-*/`へ追記します。全`result.json`をstagingへ生成し、metadataとともにrenameでpublish。旧原票を置換しません。record checkerだけが自分の一時保存領域で意図的staging failureを試し、旧byte digest保持を記録して一時領域を片付けます。電源断・disk full・実storageの耐久性検証ではありません。

## 予想 → 操作 → 比較 → 原典／実装 → 答え

1. 「負荷がちょうど1ならmissする？」と予想し、boundary/horizon12で計算する。
2. miss0、B1はfinish=deadline=12、lateness0を確認する。deadlineと同時の完了はmissではない。
3. normalへ変える。U=3/4、全jobが期限内完了、idle区間がある。eventを戻すとt8のB1 preemptionとA2実行を確認できる。同deadlineのtie-breakを含む。
4. overloadへ変える。U=5/4、A1のdeadline8にremaining1が残る。flagはt8からlatched。A1はt9に完了、lateness=1となる。
5. 「最初のmiss／flag」で戻す。t8ではA1のfinishは未確定で「—」、後のfinishを現在stateに混ぜない。timeline全体はfinite runの全結果で、黒線／表／event flagが現在のeventを示す。
6. horizon24/36へ延ばす。overloadはmissとbacklogが増えるが、flagはt8から一度だけlatched。flag後も診断計算を続けており、実装置のsafe-state達成ではない。
7. raw ledger、[event-driven runner](runner.py)、[1-tick Oracle](oracle.py)、[checker](test_runner.py)、以下の原典locatorで答え合わせする。

## 実行契約・Oracle・有限範囲

単一CPU、同期release t0、固定整数execution、independent tasks、relative deadline=period、preemptive、context switch／preemption overhead0、I/O／lockなし。抽象整数tickであり、実時計の秒・msや実WCET測定ではありません。優先順は最早absolute deadline、同じならtask ID A<B、さらにjob index。missした古いjobもEDFで残りを計算します。

| case | A(C,T) | B(C,T) | U=ΣC/T | horizon12の結果 |
|---|---|---|---|---|
| normal | (1,4) | (3,6) | 3/4 | miss0、未完了0、flagなし |
| boundary | (2,4) | (3,6) | 1 | miss0、B1はt12ちょうど完了 |
| overload | (3,4) | (3,6) | 5/4 | miss2、未完了1、t8 flag、max完了tardiness1 |

runnerはrelease/deadline/finishへ時刻をjumpしCPU segmentを記録します。前segmentのfinishを先に確定してからdeadlineを検査するので、同時完了をmissにしません。releaseはt<horizonだけ、deadline検査はt=horizonまで、以後のrelease／finishは生成しません。lateness=finish−deadline、tardiness=max(0,lateness)。未完了のlatenessはnullです。max完了tardinessは未完了jobの最終遅れを含みません。

独立Oracleはimmutable release一覧と累計service数から1 tickずつ選択し、runnerのjob更新／simulateを呼ばず、全CPU timelineとrelease/deadline/finish/remaining/lateness/miss/flagを照合します。small searchは先頭min(horizon,12)にreleaseかつdueのjobsだけについて、idleを含むCPU選択肢をmemoized探索し、期限内実行順の存在を確かめます。これはEDF選択と別の存在検査で、長区間や実機の全条件を証明しません。

10 unittestと3 cases×3 horizons（12/24/36）の9条件を検査。入力拒否、deadline同時完了、CPU時間保存、release前実行なし、miss重複なし、preemption、flag非解除、未完了truncation、trace決定性とOracle改竄検出を含みます。モデルtraceはhorizon≤36、検査上events≤200に限定し、無限実行やwall-clockスケジューリングをしません。

## 学習の道筋と次に問うこと

前提は整数の時間軸、区間の長さ、queueと優先順を読めることです。まずtask（周期的な仕事）とjob（1回の仕事）、release、relative/absolute deadline、finishを区別します。次にEDFのready選択とpreemption、実行需要C/T、deadline missとlatenessを学び、上の正常／境界／異常を計算します。その後、有限Oracleとの比較、何が実務判断に不足するか、未教材の実験、原典の仮定へ進みます。

この教材から判断できるのは、指定した理想モデル内で「どのjobがいつ期限を逃し、どれだけの未完了仕事が残るか」「同時完了をmissにしていないか」「flagと実処理を混同していないか」です。U=1.25はこの設定の処理需要と1 CPU時間が矛盾する例です。miss0やflag=trueだけでは、実設備への採用、安全装置の設計・認証を判断できません。実務の採用判断には以下の未教材が残ります。

次の3実験は**未実施の学習計画**であり、今回のrunnerに機能を追加したとは扱いません。現runnerは別deadline/jitter/lock入力を受け付けません。

| 主要未教材概念・問い | 次の有限実験案と観測 | 公式locator |
|---|---|---|
| WCET、release jitter、D≠T：平均負荷だけで判断できる？ | boundedなexecution変動とrelease offset／短いdeadlineの列を別モデルに与え、需要・miss・latenessを比較する。実WCET測定・全jitter保証は別途必要 | [Linux Deadline §3.1 Definitions／§3.2 Uniprocessor analysis](https://docs.kernel.org/scheduler/sched-deadline.html#definitions)、§3.4 parameters |
| blocking、priority inversion、PI：readyなのにCPUを得られない理由は？ | syntheticな低／中／高priority 3 taskと1 lockの有限traceで、lock待ち、priority inheritance有無、blocking時間を比較する。現在の2-task EDFへPIを実装済みとはしない | [Linux RT-mutex design: Unbounded Priority Inversion／Priority Inheritance](https://docs.kernel.org/locking/rt-mutex-design.html#priority-inheritance-pi) |
| hazard、safe-state response、assurance：flagだけでhazardが制御されたか？ | 機器を接続せず架空のhazard・要求・出力状態を分けたstate modelを作り、入力故障・検出遅延・出力故障のnegative traceと要求→検証の対応を検討する。実機・risk受容・認証判断は未実施 | [NASA SWEHB Ver D SWE-134](https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695493/SWE-134%2B-%2BSafety-Critical%2BSoftware%2BDesign%2BRequirements): §1 Requirements a/j/l、[Software Safety and Hazard Analysis](https://swehb.nasa.gov/spaces/SWEHBVD/pages/140641657/Software%2BSafety%2Band%2BHazard%2BAnalysis): hazard report／control／verification |

RTOS/実OS、multicore、clock/interrupt、fault tolerance、safety lifecycleは[coverage](coverage.json)で引き続き未教材です。上の実験案はその全領域を網羅せず、分野全体完成へのcreditを持ちません。

## 一次資料locator（2026-10-05 JST閲覧）

- [C. L. Liu & J. W. Layland, *Scheduling Algorithms for Multiprogramming in a Hard-Real-Time Environment*, JACM 20(1), 46–61 (1973)](https://www.cs.ru.nl/~hooman/DES/liu-layland.pdf)、[DOI](https://doi.org/10.1145/321738.321743)。刊行p48 / PDF p3のSection3 (A1–A4)とpreemption説明、刊行p55 / PDF p10のSection7 deadline-driven priority、刊行pp56–58 / PDF pp11–13のTheorem7と仮定付き証明。論文の理想モデルに対する解析と、この有限観測、実機保証を区別します。
- [Linux Kernel *Deadline Task Scheduling* §2.1 Main algorithm](https://docs.kernel.org/scheduler/sched-deadline.html#main-algorithm)、§3.4 Relationship with SCHED_DEADLINE Parameters。LinuxのEDF+CBSとadmission等は本教材と異なります。参照のみでOS policyを設定・計測しません。

第三者本文・図・code exampleは保存／転載せず、書誌・URL・locatorだけを保持します。安全性分類、hazard analysis、認証基準、実デバイス保証の一次資料網羅は未実施です。

## 原票・Skill・未教材

`result.json`はinput/plan、job ledger、segment、全event state、safe-state flag、Oracle期待値、実行UTC時刻、Python/platform、command、source SHA256を含みます。`metadata.json`はinput/plan/artifact digest、byte数、実装7ファイルのSHA256を持ちます。日付・環境情報は観測の識別子で、実real-time測定ではありません。

[QA記録](QA.md)と[module Skill](skills/atlas-real-time-safety-critical/SKILL.md)を参照してください。Skillは既存runner/checker/UIだけへrouteし、global installはしません。[coverage.json](coverage.json)は本Subjectの未教材と他の全Subject credit0を維持します。

RTOS、Linux policy、WCET、interrupt/jitter、multicore、locking、fault tolerance、機器safe-state、safety certificationは未実証です。Repository/Subject全体のcomplete、Core Graph/Gate、旧Argo Goal再開、commit/push/公開を意味しません。
