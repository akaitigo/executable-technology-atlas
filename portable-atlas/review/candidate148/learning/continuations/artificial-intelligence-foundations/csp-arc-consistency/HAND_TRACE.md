# Atlas：実装前の4条件の手計算

[期待JSON](expected.json)は以下の手表を構造化したものです。producerも模型実装もない時点で固定しています。[固定時点](records/expectation-fixed.json)へ。

| 条件 | FC後A/B/C/D | AC-3後A/B/C/D | AC-3終端 | 全解 |
|---|---|---|---|---|
| 鎖・A=0 |0 / 1 / 01 / 01|0 / 1 / 0 / 1|arc-consistent|0101|
| 三角・A=0 |0 / 1 / 1 / 01|0 / 1 / 空 / 01|inconsistent|なし|
| 三角・自由 |01 / 01 / 01 / 01|同じ|arc-consistent|なし|
| 四角・自由 |01 / 01 / 01 / 01|同じ|arc-consistent|0101,1010|

01は候補集合[0,1]、0/1はsingletonで、ここでは探索中のassignmentを表しません。A=0は入力側の固定制約です。

## 鎖：未割当間の削減

初期queueはAB,BA,BC,CB,CD,DC。ABはA0にB1のsupportがあり削減なし。BAはB0を削りB1へ。追加候補CBは既にqueueにあります。BCはB1にC0があるため変化なし。CBでC1を削りC0へ、追加候補DCは既にqueue内。CDはC0にD1があるので変化なし。DCはD0を削りD1になります。

6回のrevision、support比較は2+2+1+2+2+2=11。削除3、実再追加0、既存queueのskip2。FCはAとBの2候補だけを調べ、C/Dへ進みません。

## 三角・A固定：残queueを処理せず止める

初期queueはAB,AC,BA,BC,CA,CB。AB/ACは削減なし、BAでB0を削除してB1。BCではまだC0がsupportとなります。CAでC0を削るとC1になり、すでに処理したBCを再追加します。残queueはCB,BC。CBはC1にB1のsupportがなくCが空になり停止。残るBCは未処理です。

6回のrevision、比較2+2+2+1+2+1=10。削除3、再追加1、skip1、空停止1です。FC後のB1/C1は非空でもBCを満たせません。

## 自由な三角と四角

各arcのtail値0にはhead値1、tail値1にはhead値0がsupportです。各revisionは0対0（false）、0対1（true）、1対0（true）の3比較。三角は6arcで18比較、四角は8arcで24比較。削除/再追加はありません。

それでも三角の全解はありません。Aと異なるB/Cが同色になりBCを破ります。四角は0101と1010の2解があります。局所supportを別々に選べることと、全制約を同時に満たす一つの割当を選べることを分けます。
