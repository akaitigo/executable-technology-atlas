# producer実行前の独立期待

sceneは固定、直線中心routeは(0,0)→(4,0)。長さ・radiusはmodelの座標単位で、実メートルを測った証拠ではない。obstacleは閉rectangle、円footprintも閉集合。**distance≤rなら接触を含めcollision**、distance>rだけclear。

| scene | routeと元obstacleの最小距離² | radius0 / 1/4 / 1/2 / 3/4 | 意図異常sample判定 |
|---|---|---|---|
| narrow-width1 | 1/4 | CLEAR / CLEAR / COLLISION(contact) / COLLISION(overlap) | 端やsample点自体も壁まで1/2なので、ここでは全線分と一致 |
| wide-width2 | 1 | 全4radius CLEAR | 全4radius CLEAR |
| missed-middle | 0（x=2,y=0がobstacle内） | 全4radius COLLISION | t=0,1/4,3/4,1 → x=0,1,3,4だけは全4radius CLEAR。nearest sample distance=.9>最大radius.75 |

独立oracleは**元rectangleと中心line segmentの距離**。axis-aligned segmentの各軸intervalを分け、rect intervalとのgap dx/dyを求めてdx²+dy²をFractionで厳密比較。膨張primitiveやproducerの交差関数を呼ばない。r=1/2境界にepsilonを加えない。

producerは元rectangle⊕disk(r)の**膨張region**を作る。縦/横stripの和と4corner円の和集合に対し中心segmentの交差を判定する。円は対称なのでCobs=O⊕(-A)=O⊕A。cornerは丸い。単にx/y boundsをr増やしたboxと同一ではない。

geometryの追加手計算チェック（sceneやplannerの追加ではない）: route(0,0)→(1,0)、rectangle[7/5,2/5,2,1]、radius1/2。dx=dy=2/5、distance²=8/25>r²=1/4なのでCLEAR。膨張boxだけだと拒否してしまう。これはrounded corner primitiveを確かめる限定check。

判定は固定routeの可否だけ。COLLISIONは数学modelでの拒否で、実robotが障害物へ移動したという意味ではない。CLEARでも別routeの存在、速度、停止、安全性は保証しない。radiusの変更はmodel寸法の変更であり新plannerではない。
