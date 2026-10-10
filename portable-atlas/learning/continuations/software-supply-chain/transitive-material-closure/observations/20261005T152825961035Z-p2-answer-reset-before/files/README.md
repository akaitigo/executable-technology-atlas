# Transitive material closure — Aが同じならBも同じ？

root→A→Bの固定合成graphと入力byteを実際に読み、小さな独自artifactを生成する。直接依存名Aが同じでもBを変更するとartifactとB digestが変わり、全material照合は拒否する。5条件でartifact生成、未知node/cycleの2条件でbuild前拒否、1条件で読取失敗を観測する有限教材。

読む順は[元Subjectのdigestとbaseline](../../../subjects/software-supply-chain/README.md) → [LEARNING_PATH実験2](../../../subjects/software-supply-chain/LEARNING_PATH.md) → [直前workflowのinput/cache binding](../../workflow-batch-orchestration/interval-input-version-reuse/README.md) → [本UI](index.html)。元教材は独立期待値の必要性、workflowは区間/内容binding、本単元は固定推移material全体の到達と申告を扱う。

前提はgraphの到達集合/cycle、UTF-8 bytes、SHA256、JSON、独立期待値。root=ROOT改行、A=A1改行、B=B1改行。B変更はB2改行。Artifact recipeは到達IDをsortし、`ID:byte長:exact bytes`を連結する独自形式。root/A/BならA→B→root順のbyte列となる。[expected-table.json](expected-table.json)はproducer実行前に固定集合とartifact/materialのliteral hexを別記述し、checkerはgraph遍歴を共有しない。

正常consumerは申告集合=実到達集合=固定期待集合{root,A,B}を求め、申告digest・実読取digest・別保持baseline digestをすべて照合する。故障consumerは同じgraph検証/buildを使い、直接名が[A]であることだけを確認する。受信申告から期待baselineを作り直さないが、その期待fixtureの選定・保護・consumer自身の信頼は仮定。

B-changedでは新Bを正しく申告しても旧期待Bとの差でnormal deny、直接名故障はallow。これは更新が悪意だという証明ではなく、独立期待値が旧入力のままであることを示す。B-undeclaredはbuildでBを読んだのに申告集合にBがなくrefuse。A→B edge欠落は実到達集合からBが消えたためexpected-closureをrefuseする。未知X/cycleはmaterial読取とbuild前に両版refuse。B fileなしはexecution-error、partial読取attemptは保存するがartifactを出さない。

UIは保存原票reader。予想→条件→実到達/申告/Bdigest/生成artifact→全materialと直接名のdecision→原典/実装/raw→答え→次coverageの順。条件変更では予想を空に、予想だけ変更では新値を保持し旧応答・比較・答え・traceを消す。成功後のbuild前拒否/読取失敗では旧artifactを表示せず、読取失敗の正常答えを隠す。policy拒否でも実際に生成したartifactは観測として表示し、build成功とconsumer許可を分ける。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
PYTHONDONTWRITEBYTECODE=1 python3 runner.py  # defaultはread-only checker
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record  # 明示時のみfresh observations
python3 -u -m http.server 0 --bind 127.0.0.1  # 専有loopback、Ctrl-C終了
python3 route.py B-change
```

[experiment.py](experiment.py)が実JSON graph、専有input bytes、申告、別保持baselineを読む。[checker.py](checker.py)は固定集合/literal bytes/hash/size/decision、5改竄対照を検査しproducerをimportしない。hash primitiveは同じstdlib hashlibで、別暗号実装ではない。明示runnerはfresh runへcommand/stdout/stderr/exit、fixture snapshot、5実artifact.bin、raw/source/artifact hashを保存する。通常checker/runnerは既存receiptを更新せず全hash/mtime不変。[qa/README.md](qa/README.md)に実IAB・capture制限を保存する。

[SLSA v1.2 Build Provenance](https://slsa.dev/spec/v1.2/build-provenance)のBuildDefinition/resolvedDependenciesはbuild入力artifactの記録と再帰的分析への道筋を示す。完全性は少なくともBuild L3までbest effortとされ、本教材の固定集合完全照合は独自policy。署名なしの教材JSONをSLSA attestationや適合認定にしない。確認2026-10-05、URL/locatorだけを[sources.json](sources.json)へ保存し第三者本文を転載しない。

[有限coverage](coverage.json)の次はpackage resolverと版選択、署名/builder trust、SBOM/CVE、toolchain/hermetic build、分散artifact storage。本実験はSLSA署名・真正性・resolver・SBOM・level、registry/download、実運用・耐久性を未実証。Skillは7入口/4除外の構造のみでモデル挙動は未実行。Subject/Atlas全体の完成、Core/fullGate、公開/commit/pushは対象外。
