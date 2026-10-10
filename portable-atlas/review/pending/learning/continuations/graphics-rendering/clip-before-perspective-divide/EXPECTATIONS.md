# 有限契約と手計算（実装より先に固定）

問い: 同次座標の近面clipをdivideの前に行うと、残る多角形と面積はどう変わるか。
入力は頂点3個、各4成分x,y,z,w。成分は整数またはp/qの文字列（各整数の絶対値20以下、分母1..10）。余分なキー、浮動小数、bool、ゼロ分母は拒否。w>0、-w<=x,y<=w、z<=wが全頂点で成立する場合だけ計算する。近面はz>=0、境界を含む。side/far clipは実装しない。

near_clip / no_clip / drop_outsideの3方式を常に比較する。no_clipは全頂点をdivide、drop_outsideは内側の原頂点だけを残す故障対照。near_clipだけ辺交点を作る。交点はt=zA/(zA-zB)、P=A+t(B-A)の4成分すべてを補間し、各点のx/w,y/w,z/wを得る。属性補間は対象外。

多角形は連続重複と閉じ重複を除き、元の巡回方向を保ったまま有理数4tupleの辞書順最小点から開始する。3点以上なら先頭点fanで再三角形化。0点EMPTY、1..2点INSUFFICIENT、3点以上で投影signed area=0ならDEGENERATE、それ以外FILLED。面積はNDC XYのshoelace絶対値/2。cwはsigned areaが負。pixel coverage、culling、depth testは実装しない。投影degenerateは受理するが埋めた面積を主張しない。w<=0は処理前拒否。

|条件|近面交点（x,y,z,w）|near/no/drop面積|near fan面積|
|---|---|---|---|
|one-outside|(-1/4,0,0,1)、(0,-1/2,0,1)|3/8、1/2、0|1/8、1/4|
|two-outside|(-1/4,0,0,1)、(1/4,0,0,1)|1/8、1/2、0|1/8|
|variable-w|(-1/2,-1/4,0,3/2)、(-1/4,-3/4,0,3/2)|4/9、1/2、0|1/9、1/3|
|all-inside / exact-near / all-near|追加交点なし|1/2、1/2、1/2|1/2|
|all-outside|なし|0、1/2、0|なし|
|collinear|なし|0、0、0|0|
|near-touch|原点だけ、追加交点なし|0、1/8、0|なし|

one-outsideのAB交点t=1/2。variable-wのAB交点もt=1/2だがw=3/2、NDC=(-1/6,-1/2,0)。CA交点NDC=(-1/3,-1/6,0)。元の面積1/2から角の1/18を除いて4/9となる。w固定対可変は有限の2条件であり、全変形の保証ではない。

独立oracleは各原頂点/辺の候補を別々に集め、辺上パラメータ順で並べる半平面の凸多角形交差。producerは逐次Sutherland–Hodgman走査。oracleはproducerの関数も出力も期待値生成に使わない。上表のliteralも照合する。全6平面、GPU、D3D driver、実float丸め、UV属性補間はUNOBSERVED。
