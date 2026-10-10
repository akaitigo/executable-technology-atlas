---
name: atlas-data-science-statistical-learning
description: この1特徴OLS教材でtrain-only fitとholdout混入fit・候補選択leakageを比較し、係数・残差・MSEをPythonと独立Fraction oracle、操作UIで確かめる。多変量や他の学習方式、現実予測は未実装として区別する。
---

# OLSとholdoutの役割を確認する

rootは[教材](../../README.md)。module内の既存runner/checker/UIだけへrouteし、依存install・他Repository・公開へ広げない。

- 正常OLSの質問：rootで`/usr/bin/python3 -B lesson.py --case train-only`。係数とtrain/holdout別MSE、fit row ID、独立oracleへ接続して答える。
- leakage比較：`--case fit-leakage`または`--case selection-leakage`。低いholdout MSEを独立test性能として回答しない。候補はtrain OLSの切片へ0/1/2を加える固定集合。
- 観測再検査：`/usr/bin/python3 -B verify.py`。既定はread-only。原票更新は利用者が求めたときだけ`lesson.py --record`や`verify.py --record-*`。
- 操作：`/usr/bin/python3 -B lesson.py --port 0`で専用loopbackを起動し、表示URLとOLS title／`train-data` field IDを確認する。予想→操作→Plot/MSE/lineage→原典→答え。自分のserver/tabだけを終了する。

trainが空／一定x、invalid入力は拒否。固定追加評価をfit・選択へ渡さず、x範囲外の点数と未検証の汎化境界を区別する。MSEはnで割り、残差分散のn−2と混同しない。

random forest、classification、多変量、CV、因果推論、実データなどはrunnerにない。[Coverage](../../README.md#subject内のcoverageと未教材領域)を示して未教材と答える。別方式を固定3候補へ置換したり、toyの結果から現実性能を保証したりしない。
