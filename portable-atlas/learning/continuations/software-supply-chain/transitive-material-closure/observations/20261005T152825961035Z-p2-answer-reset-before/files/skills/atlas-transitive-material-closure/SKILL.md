---
name: atlas-transitive-material-closure
description: 固定root→A→Bの推移material bytesと申告/期待集合を比較する有限教材。SLSA署名・真正性・resolver・SBOM・level認定には使わない。
---
README・contracts.json・expected-table.jsonを読み、route.pyの7入口へ対応づける。予想→graph/申告→実artifact/Bdigest→正常全material/直接名故障→原典→答えを辿る。
正常policyは申告集合・実到達集合・別保持の期待集合を一致させ、全入力digestを照合する。直接名Aが同じでもB変更でartifactは変わる。未申告Bと到達できないBを区別する。未知node/cycleはbuild前に拒否し、読取失敗ではartifactと正常答えを表示しない。
checkerは固定集合と別記述literal byteの独立照合でproducer遍歴を共有しない。通常checker/runnerは全hash/mtime不変、stdoutだけ。明示再記録だけrunner.py --recordでfresh runと実artifact filesを保存する。
UIは保存reader。条件変更と予想だけの変更で旧比較/答え/traceを消し、新予想は保持する。build完了とconsumer許可を同一視しない。B更新の拒否を悪意の証明にしない。
SLSA resolvedDependenciesの完全性はbest effort。本独自の固定閉包policyをSLSA要件・levelへ一般化しない。hashは真正性を保証しない。署名、builder trust、resolver、SBOM、registry、外部effects、権限/課金/公開は未対応でREADME次coverageへ。
