# 依存・失敗・retryを有限DAGで比べる

標準Pythonによる逐次runnerで、dependencyが成功するまで下流を実行しないこと、bounded retryの回復と上限、cycle拒否、成功結果を保持する再実行を学ぶ1教材です。Airflow等の製品、scheduler、永続worker、実分散処理の実証ではありません。

## 最短の再現

このmoduleディレクトリで実行します。実行環境はCPython 3.9.6 / Darwin arm64。Python 3.9は保守終了済みです。追加依存はなく、保守中Pythonでの追試は未実施です。

```sh
python3 -B test_runner.py
python3 -B runner.py --case normal
python3 -B runner.py --case fail-once --retries 1
python3 -B runner.py --case always-fail --retries 1
python3 -B runner.py --case cycle
python3 -B runner.py --case normal --reuse
python3 -B serve.py
```

別ターミナルでサーバーを維持し、`http://127.0.0.1:18773/`を開きます。終了はCtrl-C。loopbackはUIからPython計算にだけ使い、task間の通信・外部サービス・subprocessはありません。

通常のrunner/checkerはstdout/stderrだけで、原票やbytecodeを更新しません。保存が必要な場合だけ`--record`を付けます。

```sh
python3 -B runner.py --case fail-once --retries 1 --record
python3 -B test_runner.py --record
```

保存先は固有UUIDの`observations/run-*/`または`checks-*/`。UIの実行buttonも`ui-*/`へ追記します。既存原票を置換しません。`result.json`はinput、graph、全lifecycle event/state、task call、再利用前の結果、Oracle、時刻・環境・commandを含み、`metadata.json`はinput/plan/source/artifact digest、byte数、実装6ファイルのSHA256を持ちます。record modeのcheckerだけが一時保存を使って保存障害を検査し、自分の一時領域を終了時に除去します。

## 予想 → 操作 → 比較 → 原典／実装 → 答え

1. retry上限1、seed2で「Bが一度失敗したらDはblockedになる？」と予想する。
2. 「Bは最初の1回だけ失敗」を実行する。Bはattempt1でretrying、attempt2でsucceeded。Dの結果は9となる。
3. 「最初の失敗／拒否」で途中へ戻す。Dはまだpending。event sliderを進め、Bの成功前にはDがstartedにならないことを確認する。
4. 同じ入力で「Bは全許可attemptで失敗」を新規runする。Bは2 attemptsでfailed、Cは成功、Dはblockedでattempt0。下流を無条件に動かすモデルではない。
5. 一度だけ失敗するcaseでretry0へ変えると失敗、retry1/2なら回復する。上限を増やしても継続失敗caseは回復しない。
6. cycleを選ぶと有効topological orderは0、全taskはpendingのまま、task呼出し0でrejected。正常graphにD→Aを追加するためAの未実行operationもDのsumに変える。
7. 正常run後、入力を変えず「直前runの成功結果を保持／再利用」。結果は同じ、今回のattemptとtask呼出しは0。新規runに戻すと4 taskを再計算する。seed等を変えたまま再利用すると拒否し、直前の原票・画面を保持する。
8. raw JSON、[runner](runner.py)、[checker](test_runner.py)、以下の一次資料locatorで答え合わせする。

## モデルの契約と有限Oracle

依存はA→B、A→C、B→D、C→D。A=seed、B=2A、C=A+3、D=B+C。seed2なら2/4/5/9。全taskはneutralなpure整数計算です。Bの失敗は指定attemptに限ったsynthetic `ArithmeticError`で、業務の処理を中断したものではありません。

runnerはKahn式にready nodeをアルファベット順で1個選ぶ逐次実装。stateはpending→ready→running→succeeded、失敗して予算があればretrying→running、予算終了でfailed。先行taskの最終stateが成功でなければblocked。cycleはtask開始前に全graphを拒否します。1〜6 taskの厳密入力validationを持ちますが、UIは上の4 taskだけです。

独立Oracleはrunnerの`topology()`、`invoke()`を呼ばず、4! = 24 permutationsから全edgeを満たす順を選び、再帰的な数式でstate/value/attempt期待値を求めます。有効順はA,B,C,DとA,C,B,Dの2つ。両方が有効でも実runnerは前者だけを実行し、並列性は主張しません。12 unit検査内でseed1/2/9 × 4 cases × retries0/1/2の36条件を照合しています。これは全workflow/製品の網羅検証ではありません。

retry上限は**再試行数**で、最大attempt数はretries+1です。delay/backoff/timeoutはモデル化せず、sleepもしません。再利用は同じplan/sourceの決定的pure結果だけをOracleで検証し、成功のみをコピーします。previous結果は変更しません。失敗の新runではattempt予算を再設定するため、複数run合計は単run上限を超え得ます。retryや再実行は外部side effectのexactly-once、idempotency、crash後の復旧を保証しません。

保存は新しいstaging directoryへ全ファイル生成後renameします。意図的staging障害で前の原票digest不変を検査していますが、電源断・disk full・分散storage耐久性を試験したものではありません。stagingが残れば未publishとして区別し、旧原票を成功runに見せ替えません。

## 一次資料locator（2026-10-05 JST確認）

- [Python 3.9 graphlib公式](https://docs.python.org/3.9/library/graphlib.html#graphlib.TopologicalSorter): 冒頭のtopological order定義とDAG条件、`prepare()`のcycle検査、`get_ready()`、`static_order()`の順序非一意、`CycleError`。これはgraphの順序であり、先行処理の成功を保証するAPIではありません。本教材はgraphlibを実runnerとして使いません。
- [Apache Airflow 3.3.2 Tasks公式](https://airflow.apache.org/docs/apache-airflow/3.3.2/core-concepts/tasks.html): `#relationships`のdefault先行成功条件、`#task-instances`の`upstream_failed`/`up_for_retry`、`#how-it-works`のretry上限。比較のlocatorのみで、Airflow互換実装・製品起動を主張しません。

本文・第三者図・code exampleは保存／転載せず、URL・版・locatorだけを記録します。製品のstateと本教材の独自stateを同一視しません。

## 記録・Skill・未教材

[QA記録](QA.md)に実IAB画面、raw binding、検査・保存障害・cleanupがあります。[module内Skill](skills/atlas-workflow-batch-orchestration/SKILL.md)は既存runner/checker/UIだけへrouteします。global installはしません。

[coverage.json](coverage.json)はこの有限教材の範囲とSubject未教材領域、他の全Subjectへのcredit0を明示します。scheduler、永続worker、queue、並列・分散実行、recovery、backfill、calendar、業務side effect、製品固有機能、production運用は未教材です。Repository/Subject全体のcomplete、Core Graph/Gate達成、旧Argo Goalの再開、commit/push/公開ではありません。
