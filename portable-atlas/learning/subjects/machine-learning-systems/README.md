# MLシステム — model artifactと入力の意味を揃える

このrepoから対象分野を学ぶための入口。現在は固定numeric modelのschema/version付き推論の有限1教材。手で決めた係数を使い、学習・実MLOps service・LLM・本番配信は実装していない。値は架空のsynthetic_scoreで、学習成果や現実の成績を予測するモデルではない。

## 学習の道筋

1. **前提**：JSON、配列順序、辞書、線形式、平均・母標準偏差、SHA-256を知る。モデルの数式だけでなく、各値の名前・単位・versionが入力の意味を決める。
2. **主要概念・仕組み**：artifact→契約照合→値検査→計算→出力のpipeline。artifactはformat/model/schema version、feature順、係数、bias、数値域を持つ。入力は要求するmodel/schema versionを持つ。hashは同じbytesの確認であり、作者の信頼や正しさの証明ではない。
3. **今回実装・正常異常**：[視覚入口](index.html)で予想→操作→比較し、[pipeline](pipeline.py)と[独立oracle](verify.py)を読む。strictとnaiveを切り替え、拒否が計算前に止まることを見る。
4. **実務判断**：数値が返ることと正しいfeatureを使ったことを分ける。契約不一致は黙ってcast/並べ替えず拒否する。並べ替えadapterを作るなら、対応表とversionの別契約が必要。入力統計の差と品質低下も分ける。
5. **限界**：本例には訓練データ、精度評価、閾値検出、alert、再学習、自動配信、registry、SLOはない。固定入力の統計からdrift検出保証や精度劣化を主張しない。
6. **原典→次の学び**：[source binding](sources.json)と[coverage](coverage.json)を使い、feature変換→評価→監視→rollbackの順で次の4実験へ進む。

## 予想→操作→比較→原典/実装→答え

予想：同じ意味の値を順序ごと入れ替えても同じ出力になるか。schema versionが違っても2数値なら安全か。入力平均が変われば必ず品質が低下するか。

module directoryで実行する。Python標準ライブラリのみ、Mac直接、外部API・新依存なし。

```sh
python3 verify.py
python3 serve.py --port 0
# 表示された127.0.0.1 URLを開く。終了はCtrl-C。
python3 route.py schema
python3 route.py production-deploy
```

操作：[UI](index.html)でcase、strict/naiveを選び、traceを一段ずつ進める。画面は実行済み[原票](observations/raw.json)の再生で、ライブ推論や実時間の性能測定ではない。

比較：固定式は `1 + 2×hours_studied + 0.5×practice_tasks`。schemaは `[hours_studied, practice_tasks]`、両値は有限数値0..100。

|入力|strict|naive|独立の意味に沿う手計算|
|---|---|---|---|
|正常 [3,8]|11|11|1+6+4=11|
|順序ごと交換 names=[tasks,hours], values=[8,3]|名前/順序拒否|18.5（意図したsilent wrong）|同じ意味なら11|
|未知schema/model version|拒否|11を返す|未知契約の意味は未定義。11が正しいとは言えない|
|1featureだけ|拒否|拒否|長さ不正|
|名前重複|拒否|11を返す|意味を一意に復元できない|
|[0,0] / [100,100]|1 / 251|同じ|境界は含む|
|string、bool、非有限、域外|拒否|拒否|naiveでも値安全検査は残す|

原典/実装：[scikit-learnのInconsistent preprocessing](https://scikit-learn.org/stable/common_pitfalls.html)を、推論でも同じfeature空間を保つ原則として読む。[Model persistence](https://scikit-learn.org/stable/model_persistence.html)でartifact互換性・信頼を学ぶ。これらのライブラリ自体を今回実行したわけではない。自作[pipeline.py](pipeline.py)のcontract段と[手計算oracle](verify.py)へ対応させる。

答え：順序の意味を検査しない計算は18.5を返すが、名前から復元した手計算は11。version拒否は意味が分からない入力を計算へ通さない境界である。要求version文字列の検査は署名やartifact registryの承認とは違う。

## 固定new inputの分布比較

referenceは `[[1,2],[2,4],[3,6],[4,8]]`、new_inputは `[[10,2],[11,4],[12,6],[13,8]]`。両方ともschemaを満たす。hours平均は2.5→11.5、tasks平均は5→5、出力平均は8.5→26.5。母標準偏差・最小・最大・nも表示する。

[TFDVのschemaとdrift/skew](https://www.tensorflow.org/tfx/data_validation/get_started)は集合比較と入力契約の違いを学ぶ原典。今回の比較は4行ずつの記述統計のみ。ラベルや基準閾値がなく、p値、分布同一性検定、drift detector、精度低下の判定ではない。

## Subject主要未教材coverage

[TFX公式pipeline guide](https://www.tensorflow.org/tfx/guide)を全体の見取り図に使う。単に「全Subject未完」とせず、次に問うことを[coverage.json](coverage.json)で原典locatorへ対応させる。

|領域|次に学ぶ概念・問い|状態|
|---|---|---|
|データ取得・管理|batch/stream、lineage、dataset version、ラベル。同じデータを再取得できるか|未教材|
|feature/schema|欠損、単位、fit/transform、leakage、train/serve skew。意味は揃うか|型・名前・順・versionのみ|
|学習再現|split、seed、hyperparameter、tracking、checkpoint。差を説明できるか|未教材|
|評価・承認|holdout、slice、calibration、gate。悪化を見逃さないか|未教材|
|artifact/registry|format、環境互換、署名、promotion。hash一致で十分か|JSONとdigestのみ|
|serving|batch/online、serialization、latency/throughput、cache、concurrency。負荷で変わるか|ローカル関数のみ|
|観測/shift/再学習|統計、drift/skew、ラベル遅延、concept drift、trigger。平均差から何が言えるか|記述統計のみ|
|運用・復旧|CI/CD/CT、canary/shadow、rollback、SLO、監査。組を戻せるか|未教材|
|信頼/privacy/資源|artifact trust、入力保護、PII、アクセス、cost。誰が何を読めるか|未教材|

次の4実験（未実装）：①trainだけでfitした変換とtest混入を比較（[features原典](https://scikit-learn.org/stable/common_pitfalls.html)）、②小holdoutとslice別手計算で2候補の評価gateを比較（[lifecycle原典](https://www.tensorflow.org/tfx/guide)）、③同平均・異分散batchでhistogramとschema違反を分ける（[data validation原典](https://www.tensorflow.org/tfx/data_validation/get_started)）、④model/schema/変換の組を2version用意しatomic切替と部分rollbackを比較（[artifact原典](https://scikit-learn.org/stable/model_persistence.html)）。

## 再現証拠と検査

[inputs](inputs.json)、[model](model.json)、[raw](observations/raw.json)、[receipt](observations/receipt.json)を結合。receiptは実行UTC時刻・Python/OS/architecture・input/model/source/artifact SHA-256を持つ。rawはstrict/naive trace、意味に沿う独立手計算、拒否、batch統計を保存。nonfinite試験入力はJSONで表せないため明示tagで記録する。

通常 `python3 verify.py` はread-only。原票更新だけ明示 `python3 verify.py --record`。独立oracleは本体のschema validatorや計算を呼ばず、literal契約と名前付きFraction手計算、rational統計で照合する。100個のseed固定正常入力と順序交換も検査する。README/Skillのlocal links、roadmap/source bindingも確認する。[Skill](skills/atlas-machine-learning-systems/SKILL.md)のrouteは既存checker/UIのみ。作者routing smokeを独立AgentEvalと呼ばない。

[実IAB QA](observations/ui-qa.json)と[検証記録](VERIFICATION.md)は実画面確認・capture保存可否・owned resource cleanupを区別する。この有限1単位でSubject全体やAtlas全97入口の完成を主張しない。
