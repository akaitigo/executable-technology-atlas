---
name: atlas-orchestration-taint-selector-eligibility
description: Atlasの固定配置条件で、容量・nodeSelector・taint許容と候補選択を分けて読む。実クラスタ操作や配置保証には使わない。
---

# Atlas｜配置を妨げる条件を読むSkill

[読む順](README.md)→[元slot](related.html?topic=slots)→[CPU・memory](related.html?topic=resources)→[契約](CONTRACT.md)→[画面](index.html)→[原典](SOURCES.md)→[範囲](COVERAGE.md)へ進みます。[確認状態](qa/reader-acceptance.json)で手期待・計算・GUIの実施状態を先に分けます。[実装前の手期待](expected.json)と[保存した初回計算](observations/run-01/results.json)を、以下のcase IDで対応させます。保存結果readerのGUIで同じ値と資料リンクを確認済みです。有限3問を独立担当が資料と保存値へ辿った確認であり、未知の問いに対する一般Agent評価ではありません。

1. 「容量が空いているのにPendingなのはなぜ？」にはselector-onlyを使う。Aはlabel条件、Bは未許容taintで除外される。CPU・memoryだけの旧教材へ戻り、容量増設でこの条件が消えるとは判断しない。
2. 「tolerationを足したら専用nodeに行く？」にはtoleration-onlyとselector-and-tolerationを比べる。前者はA/Bが候補で教材順A、後者はBだけ。capacity-blockは条件が合ってもCPU残量が不足する。feasible集合と選択順を混同しない。
3. 「BOUNDならpodは応答できる？」には故障版のselector-only／wrong-toleration-valueで、選択nodeがfeasible集合外であることを確認する。正常版のBOUNDも模型の選択までで、実Ready・probe・通信は[未対応範囲](COVERAGE.md)へ案内する。

固定6条件と4拒否を未知のクラスタ状況へ当てはめません。kubectl、Docker、SDK、実node設定の変更を開始しません。この有限3問の資料利用を一般Agent評価やKubernetes適合性へ換算しません。
