# Bell状態と古典相関mixture

前提: [第一単元の純粋・混合状態](../../../subjects/quantum-computing/README.md)と[学習経路の実験4](../../../subjects/quantum-computing/LEARNING_PATH.md)を接続する有限の続編です。Python標準ライブラリとブラウザを使います。基底順は00,01,10,11、先頭ビットAがcontrol、Bがtargetです。

## 予測して実行する

1. Bellと古典相関mixtureのZ分布を予測する。各局所状態がI/2なら全体も同じだろうか。
2. `python3 verify.py`で記録と独立期待値を照合する。`python3 serve.py`の表示URLで[UI](index.html)を開く。
3. ケースとZ/Xを切り替え、手順の先頭から末尾へ進む。用意した密度行列、測定基底での密度行列、部分トレース、同時確率を比較する。
4. 原典と未教材領域を開き、下の問いに自分の言葉で答える。

主要概念: |00>にH⊗I、続いてCNOT(A→B)を作用させると(|00>+|11>)/√2になる。mixtureは枝ごとの外積を確率で足す。ベクトル自体を足す操作ではない。[IBMのゲート定義](https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information/multiple-systems/quantum-information)と[密度行列の凸結合](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/convex-combinations)に対応する。

| モデル | Z同時確率 | X同時確率 | 準備時Trρ² / 判定 |
|---|---|---|---|
| Bell | 1/2,0,0,1/2 | 1/2,0,0,1/2 | 1 / 一致 |
| 古典相関mixture | 1/2,0,0,1/2 | 1/4ずつ | 1/2 / 一致 |
| control逆転(HはAのまま) | 1/2,0,1/2,0 | 1/2,1/2,0,0 | 1 / 意図と不一致 |
| 枝のベクトル平均 | 測定拒否 | 測定拒否 | 1/4、trace=1/2 |
| ベクトル平均を再正規化 | Bellと同じ | Bellと同じ | 1 / mixtureの意図と不一致 |
| 局所I/2の積で置換 | 1/4ずつ | 1/4ずつ | 1/4 / Bellの意図と不一致 |

実務判断: Bell、mixture、局所積はどれも縮約状態I/2を持つが、全体の密度行列は異なる。準備時ρ00,11はBellで1/2、mixtureで0。非対角成分は基底依存で、mixtureもX変換後にはρ00,11=1/4になる。単一成分や局所混合性を一般のentanglement判定にしない。[IBMの全体・縮約状態](https://quantum.cloud.ibm.com/learning/en/courses/general-formulation-of-quantum-information/density-matrices/multiple-systems)で確認する。

限界: 理想ゲートの古典CPU計算でありshots=0。確率の差をshot数で埋めない。手書き有理数の4×4行列を期待値とし、浮動小数との絶対誤差1e-12で照合する。各物理枝のnorm²は1、凸結合には一つの純粋ベクトルnormはない。未正規化平均のTrρ²はpurityと解釈せず、trace=1/2でBorn測定を拒否する。入力は有限の実数ベクトルと列挙モデルに限定し、任意密度行列の一般検証器ではない。実機、Bell不等式、一般のentanglement検出、量子優位性は検証していない。

原典: [source locator集](sources.json)。未教材領域と次の3実験: [coverage](coverage.json)。答え合わせ: Zと局所情報だけでは両者を区別できず、この固定モデルではXの同時分布が区別する。ベクトル平均の再正規化は正常な純粋状態を作るが、混合の意味を保存しない。

[検証記録](VERIFICATION.md) · [実測raw](observations/raw.json) · [内容hash receipt](observations/receipt.json) · [手書き期待値](hand-oracle.json) · [Skill](skills/atlas-bell-classical-correlations/SKILL.md)

実装を読む: [quantum.py](quantum.py) · [独立checker](verify.py) · [手書き期待値](hand-oracle.json)。今回のリンク追加後の閲覧確認はobservations/link-revision-qa.jsonに別記録し、旧UI/QA/receiptはobservations/link-historyに保持する。旧quantum計算のcreditを再加算しない。

ブラウザ本文閲覧: [quantum.pyを読む](source.html?file=quantum.py) · [verify.pyを読む](source.html?file=verify.py) · [期待値を読む](source.html?file=hand-oracle.json)。source viewerはファイル本文をそのまま取得する。
