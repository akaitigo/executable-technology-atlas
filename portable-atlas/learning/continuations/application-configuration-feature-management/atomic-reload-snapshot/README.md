# Atomic reload snapshot — どの版で要求を読むか

合成JSONを実際に読み、全field検証後のimmutable snapshot参照交換と、意図的なfield別更新を比べる。4更新タイミング・6入力拒否・1読取失敗の有限検証で、実OSやapplication設定を操作しない。

読む順は[元Subjectの型・優先順位](../../../subjects/application-configuration-feature-management/README.md) → [coverageのatomic reload snapshot](../../../subjects/application-configuration-feature-management/coverage.json) → 本単元の[index.html](index.html) → [関連教材のcontract失効](../../data-governance-quality-lineage/contract-evolution-invalidation/README.md)。Subjectでは入力から最終設定を作る。本単元では採用済み設定の更新中に要求がどの版を使うかを扱う。関連教材ではdatasetのcontract変更と再評価を扱う。

v1=(timeout_ms=1000,retries=2)、v2=(2000,4)。versionは有限文字列labelで、単調増加deployment規則ではない。JSON objectのfield集合を厳密に照合し、timeout_msはboolを除くint 1..5000、retriesはboolを除くint 0..5。候補を一度検証してfrozen dataclassへ変換した後だけ採用する。候補label、検証済み候補版、採用版、拒否理由は別々に表示する。

正常版は1つの参照を交換し、要求開始時のsnapshotを2field読取まで保持する独自契約。要求途中でv2を採用してもその要求はv1=(1000,2)、次要求はv2=(2000,4)。故障版は各fieldを別々に読む・書くので(1000,4)や(2000,2)が現れる。これはどの採用版のtupleにも一致しない。threading.Eventのreached/release gateで順序を固定し、sleepや偶然のタイミングに頼らず実thread読取/更新を実行する。Python全実装、多process、CPUメモリモデル、分散atomicityを証明する実験ではない。

不正候補v3の型/範囲/bool/版/field/JSON構文を拒否して採用v2を保持するlast-known-goodも独自契約。対照は両版ともv2の読取で残す。候補ファイルなしは入力拒否とは分けてexecution-errorとし、request=null、正常答えなし。読み取れなかった候補の内容や正常結果を捏造しない。

UIは保存原票reader。予想→条件操作→正常/故障・拒否理由・版→原典/実装/raw→答え→次coverageの順。条件変更では予想を空に、予想単独変更では新予想を保持し、旧比較/答え/traceを消す。拒否時も採用v2の対照を表示する。ブラウザの比較buttonは実reloadしない。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 checker.py   # 全hash/mtime不変の独立照合
PYTHONDONTWRITEBYTECODE=1 python3 runner.py    # defaultは同じread-only照合
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record  # 明示した再記録だけ新run
python3 -u -m http.server 0 --bind 127.0.0.1   # 専用dynamic loopback、Ctrl-Cで終了
python3 route.py between-reads
```

[expected-table.json](expected-table.json)はproducer実行前の手書きtuple/版/拒否表。[checker.py](checker.py)はproducerをimportせず、採用版・要求tuple・field版・trace順序を照合し5改竄対照を検出する。通常checker/runnerはreceiptを更新しない。明示runnerのfresh observationsにcommand/exit、実JSON snapshot、raw/source/artifact hashを保存し、observation-data.jsをそのrunへ向ける。QAは別receiptで、証拠を再封印上書きしない。[qa/README.md](qa/README.md)に実IABとcapture限界を記録する。

[Python json一次資料](https://docs.python.org/3/library/json.html)のjson.load・conversion table・JSONDecodeErrorはJSON読取/変換/構文エラーを支える。確認2026-10-05のlive docsは3.14系列、実行はMacの3.9.6。使う基本APIを実機で照合した。snapshot交換とlast-known-goodはPython jsonが保証する仕様ではない。[sources.json](sources.json)にこの境界を保存する。

次coverageは複数writerの競合/旧版rollback、schema migration、remote provider timeout/cache、永続保存とrestart、分散reload。実OS設定、運用権限、remote provider、分散・耐久性・SLAは未実行。Skillは6入口/4除外の構造確認だけでモデルの自律挙動は未検証。Subject/Atlas完了やCore/fullGateの成功を主張しない。
