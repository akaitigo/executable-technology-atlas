# 有限契約・更新順と境界手表

独自無次元plant y′=(u-y)/τ、τ=1秒。y0=z0=0、Kp=1、Ki=0/1、h=.25/.5秒。t=0..8秒、r=4 (t<4)、r=.5 (t>=4)。全12条件です。上限1、下限-1。hはcontroller周期でありplant solverの刻み変更ではありません。

各step nで旧stateから e=r[n]-y[n]、q=Kp*e+Ki*z[n] を決め、区間[n*h,(n+1)*h)中はuを保持。freeはu=q、saturated/conditionalはu=max(-1,min(1,q))。y_next=u+(y-u)*exp(-h/τ)。条件付き停止は (q>=1 and e>0) or (q<=-1 and e<0) の時のみ。z_next=z (停止) または z+h*e。y_nextをe計算へ使わず、新zをqへ使いません。Ki=0でもzをこの規則で記録しますが、Ki*zは常に0で出力へ寄与しません。

| conditional / h=.5, Ki=1 | y,z,r | e / q / u | stop / z_next |
|---|---|---|---|
| 上限外向き |0,1,1|1 / 2 / 1|true / 1|
| 上限等値 |0,0,1|1 / 1 / 1|true / 0|
| 下限外向き |0,-1,-1|-1 / -2 / -1|true / -1|
| 下限等値 |0,0,-1|-1 / -1 / -1|true / 0|
| 上限だが内向き |2,3,1|-1 / 2 / 1|false / 2.5|
| 下限だが内向き |-2,-3,-1|1 / -2 / -1|false / -2.5|
| 上限でe=0 |1,1,1|0 / 1 / 1|false / 1|
| 下限でe=0 |-1,-1,-1|0 / -1 / -1|false / -1|
| 限界内 |0,0,.5|.5 / .5 / .5|false / .25|

初期step0/h=.5のPIは全方式でe=q=4。freeはu=4,y_next=1.5738773611,z_next=2。saturatedはu=1,y_next=.3934693403,z_next=2。conditionalは同じy_next、z_next=0。初期3step×12条件はhand-oracleへ先に固定しています。

整定判定は切替4秒以降のsample点、|y-.5|<=.05。最初の帯内到達first_entryを記録し、帯内→帯外の遷移を再逸脱と数えます。settledは以降全sampleが帯内、かつ終端まで1秒以上ある最初のsample。未整定はstatus=NOT_SETTLED_IN_WINDOW、settled_time=null。sample間を含めた保証ではありません。post-drop peak excessはt=4..8のsample y-.5の最大値（0以上）で、切替直後の旧stateも含めます。

最終t=8にはy/z/eを記録しますが、要求/実u・停止・次stateはnull（次区間未実行）です。全intervalとterminalを保存します。飽和はqが厳密に上下限を超えた時のclipped=true、等値停止と区別します。飽和積分継続は正しい独自modelで、windupを示す問題対照です。故障実装として偽装しません。
