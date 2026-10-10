# 実行前に固定する式と期待

plant: y'=-y+u、tau=1。比例controller K=2,r=1,y0=0、clipなし。連続feedbackなら y'=2-3y、平衡y*=2/3。

| model | 更新 / exact | deviation係数a | 漸近安定条件 |
|---|---|---|---|
| continuous-exact | y(t)=2/3(1-exp(-3t)) | sample点の比exp(-3h) | 常に減衰（このmodel） |
| forward-euler（連続閉ループの数値解） | y[n+1]=y[n]+h(2-3y[n]) | 1-3h | 0<h<2/3 |
| backward-euler（連続閉ループの数値解） | y[n+1]=(y[n]+2h)/(1+3h) | 1/(1+3h) | 任意h>0で減衰、この線形系に限る |
| sampled-hold-exact（別controller model） | u[n]=2(1-y[n]); y[n+1]=exp(-h)y[n]+(1-exp(-h))u[n] | 3exp(-h)-2 | 0<h<ln3 |

sampledの区間式: u[n]を固定して積分すると y(t[n]+s)=exp(-s)y[n]+(1-exp(-s))u[n]、0≤s≤h。連続閉ループを先に閉じてexp(-3h)とする操作とは違う。どちらもplantを厳密に積分しても、feedback更新規約が異なる。

deviation d[n]=y[n]-2/3はd[n+1]=a*d[n]。独立閉形式は y[n]=2/3*(1-a**n)。浮動小数点の反復実装と、Decimal precision80の閉形式・指数関数を別経路で照合する。初期stepはy0=0,u0=2から直接:

| h | N=T/h | forward y1=2h | backward y1=2h/(1+3h) | held y1=2(1-exp(-h)) | 事前予想 |
|---|---:|---:|---|---|---|
| .1 | 80 | .2 | 2/13 | 2(1-exp(-.1)) | 全て減衰、同じy*でも過渡は異なる |
| .2 | 40 | .4 | 1/4 | 2(1-exp(-.2)) | 全て減衰 |
| .8 | 10 | 1.6 | 8/17 | 2(1-exp(-.8)) | forward a=-1.4で発散、held -1<a<0で減衰振動 |
| 1.6 | 5 | 3.2 | 16/29 | 2(1-exp(-1.6)) | forward/heldとも発散、backwardは減衰 |

境界はforward h=2/3でa=-1、held h=ln3でa=-1（どちらも非減衰2-cycle）。T=8とT/h整数という今回fixtureに合わないため、その境界時系列を実runしたとはしない。h=.8は両境界の間、h=1.6は両境界より大きい。

T=8ではcontinuous y(T)=2/3*(1-exp(-24))。fixed Tのsolver誤差はこの値への差で示す。sampledとの差はcontroller model差でありsolver誤差と呼ばない。最終値だけで安定判定しない。判定は|a|と全時系列を使う。T終端のcontroller再計算値u(T)は次区間をrunした証拠ではない。
