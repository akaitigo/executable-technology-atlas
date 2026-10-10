---
name: atlas-quantum-computing
description: 1 qubitのH干渉と途中dephasingをcomplex Python simulationで再現・説明するローカル教材。実量子機や任意の量子algorithmの実装には使わない。
---

# 1 qubit interference教材

Skill directoryの`../..`が教材root。[README](../../README.md)で入口、[Coverage](../../COVERAGE.md)で仮定・未対応を確認する。

- 保存結果の説明は[run](../../evidence/run.json)と[raw state](../../evidence/stdout.json)から、観測時刻・環境・complex値・Born確率・sample countsを引用する。未再実行なら現在の実観測と呼ばない。
- 再観測を頼まれた場合だけ教材rootで`python3 -B observe.py`と`python3 -B verify.py`を実行。stdlibのみ。[simulator](../../simulator.py)はbranch-vector経路、[verify](../../verify.py)は別の2×2 oracle。
- [UI](../../index.html)で予想→H→D/phase比較→最後のH→保存sampleへ進む。[比較図](../../evidence/interference.svg)は実simulationの再描画でcaptureではない。

Amplitude、phase、Born probability、有限sample frequencyを区別。Dは測定結果を忘れるmixed ensemble、Z/Sはcoherenceを保つunitary操作。mixed stateを平均amplitudeのpure stateへ置換しない。実量子機や量子優位性のEvidenceではない。

Bell、多qubit、任意algorithm、実noise/quantum hardware、クラウド、実測shotの依頼は今回の未対応として不足を説明する。依存install、クラウド接続、課金、設定変更、global Skill install、外部公開へ拡張しない。
