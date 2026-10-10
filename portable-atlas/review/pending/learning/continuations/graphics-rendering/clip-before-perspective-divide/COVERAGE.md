# 実証範囲

|条件|検査・操作|
|---|---|
|1外/2外|交点・inside・NDC・fan・手面積、3方式同時表示|
|全内/全外/厳密近面/全近面|境界包含、EMPTYとFILLED|
|固定w/可変w|交点4成分、NDC、手面積、w=3/2を原票へ辿る|
|cw/collinear/near-touch|signed area、退化・1点、面積0をfillと呼ばない|
|wゼロ/負、side/far外|処理前拒否、前回図と答え消去|
|producer故障/通信503|実RuntimeError/HTTP503を別状態で表示|
|任意4入力|shift・深度・同次scale・空形状、literal+oracle+receipt|
|答え失効|条件/予想/JSON/reset、保留後変更の古い結果無視|

固定15+任意4条件。独立oracleは候補集合を辺parameter順に並べ、producerの逐次clip関数を共有しない。手literalは実装前固定。checkerは原票、source binding、UI図dataset/表/答え、別receiptを照合する。負例は出力改変と入力境界を検出する。

GPU/D3D/driver/float丸め/全6平面/属性補間/rasterization/culling/depthはUNOBSERVED。native画面は実ブラウザ観測だけ。通常CLIのread-only確認は別証拠。集約gate/Core auditはこの限定依頼では実行しない。
