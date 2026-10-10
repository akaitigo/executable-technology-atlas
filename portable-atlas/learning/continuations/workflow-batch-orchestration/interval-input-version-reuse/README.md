# Interval / input version reuse — 再利用したのはどの入力か

合成JSONのpure sum taskで、区間・入力内容を固定する再利用と、区間欠落・digest欠落・latest参照の故障を比べる。9成功条件・5入力/内容拒否・1読取失敗を4版で実行する独自local model。Airflowを起動せず、calendarや外部副作用を実行しない。

読む順は[元Subjectの有限DAG](../../../subjects/workflow-batch-orchestration/README.md) → [LEARNING_PATHの実験4](../../../subjects/workflow-batch-orchestration/LEARNING_PATH.md) → [直前Config snapshot教材](../../application-configuration-feature-management/atomic-reload-snapshot/README.md) → [本UI](index.html)。DAGでは成功結果を保持し、Configでは要求が採るsnapshotを固定した。本単元では再実行する区間と入力内容を固定し、結果のbindingがその要求に対応するかを見る。

day1/v1=[2,3]→5、day1/v2=[2,8]→10、day2/v1=[7]→7。day2/v2=[2,3]→5は区間欠落を検査する追加対照。同じ入力digestだが区間が異なるため正常版は新しく計算し、区間欠落版はday1 artifactをhitする。数値5が同じでも区間bindingは誤り。day2/v1だけではdigestも変わるので区間欠落は誤hitしない。

正常keyは(sum-demo-v1, interval, input_sha)。sum-demo-v1は固定したtask実装label。input_shaは入力整数listをcompact JSONに正規化したSHA256で、版label・区間・空白を含めない。版はmanifestによる入力参照であり、同じv1 labelでも内容が[2,8]へ置換されればdigestが変わる。空白だけ変わる対照はraw_file_shaが異なるがinput_shaは同じで正常再利用できる。

cache artifactはbinding={task,interval,input_sha}とvalue/countを持ち、artifact_shaでその内容を照合する。入力digestと保存内容digestは別物で、hash一致は真正性や承認を保証しない。正常版はhit時に要求bindingも照合する。区間欠落・digest欠落版はkeyとbindingの要求照合を意図的に省き、誤ったhitを観測する。毎条件・各版に独立cacheを作り、必要な条件だけday1/v1=5をseedする。case間の状態は混ぜない。

latest更新前/後のmanifestを実JSONとして読む。正常版の明示v1は更新後も5、latest指定はv2で10。latest-lookup故障版は明示v1でもlatestを読むため10になり、入力参照そのものが変わる。これはkey欠落による旧結果hitとは分けて表示する。

未知区間/版、boolを含む整数list、不正JSON、cache内容digest不一致はexpected-refusal。value=null、task呼出し0、cache_before=cache_afterで旧cacheを保持。候補ファイルなしはexecution-error、結果と正常答えを出さない。専有fixtureだけを読み、実OS設定・実データ・service・外部副作用を操作しない。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
PYTHONDONTWRITEBYTECODE=1 python3 runner.py  # defaultは同じread-only照合
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record  # 明示時のみfresh observations
python3 -u -m http.server 0 --bind 127.0.0.1  # 専用loopback、Ctrl-C終了
python3 route.py latest-drift
```

[固定oracle](expected-table.json)はproducer実行前に区間/版/literal合計/hit/bindingの期待値を定めた。[checker.py](checker.py)はproducerをimportせず6改竄対照も照合する。実JSON読取/resolve/key lookup/pure sum/cache content照合を[experiment.py](experiment.py)で実行し、明示runnerだけ新原票とfixture snapshot、command/stdout/stderr/exit、source/artifact hashを保存する。通常checker/runnerはreceiptを書き換えない。UIは保存原票readerで、比較buttonによる実験再実行ではない。[qa/README.md](qa/README.md)に実IAB・条件/予想reset・capture制限を保存する。

[Airflow 3.3.2 Best Practices](https://airflow.apache.org/docs/apache-airflow/3.3.2/best-practices.html#creating-a-task)のCreating a taskは、再実行で結果を変えないためにlatestを避け固定partitionを読む観点を示す。本モデルのkey、canonical digest、cache内容bindingは独自契約。data_interval_startやbackfill製品機能は実装しない。2026-10-05に本文locatorを確認し、第三者本文/図/codeは保存していない。[sources.json](sources.json)に境界を記録する。

[有限coverage](coverage.json)の次はtask実装変更、artifact真正性/expiry、calendar/backfill、分散storage、多writer競合・耐久性。Skillは8入口/4除外の構造だけを検証し、モデル自律挙動は未実行。元Subject、他continuation、Portal、Core/fullGateは変更しない。Subject/Atlas全体の完成や製品互換を主張しない。
