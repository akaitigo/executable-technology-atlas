# 独立oracle契約・訂正版 v2

2026-10-06の早期QA指摘により、旧oracle-contract.mdの総実行数と途中状態の添字混用を訂正した。旧契約と初回observationのbindingは変更しない。実装・手表・閉式checkerはもともと下記の状態列と一致する。現行の学習導線は本ファイルを参照する。

総実行数 K=min(n,budget)、加算量 s=1（normal）または2（double-y）。初期状態 x=n,y=0。

本体番号 j=1..K として：

|位置|x|y|x+y|
|---|---|---|---|
|本体の前|n−(j−1)|s(j−1)|n+(s−1)(j−1)|
|x代入直後（途中）|n−j|s(j−1)|n+(s−1)(j−1)−1|
|y代入直後（境界）|n−j|s·j|n+(s−1)j|

最終境界は x=n−K,y=sK。guard exit は K=n。境界違反は s=2 かつ K>0。guard exit のときだけ事後条件 s·n=n を評価する。budget=0,n>0は初期化のみ観測し事後条件はnull。

たとえば n=1,budget=1,normal は K=1,j=1。途中は (0,0)、境界は (0,1)。旧契約の誤読で生じる (-1,1) を使用しない。

checkerはjについて閉式で全162入力の状態列を組み立てる。calculateは反復ごとにkを増やすが、そのkは本体番号jであり、after_xではまだyは前の本体数j−1に対応する。両者の結果を全状態で照合する。

通常のchecker/runnerはread-only。観測保存はrunner --recordのみ。v2を含む新しいsource bindingは新規UTC観測として追加し、旧世代を上書きしない。
