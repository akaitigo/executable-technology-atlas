# Atlas：容量を増やさず、置ける場所を増やす

目標09。既存180教材を基準とし、読み出しdirect-mappedを前提に、同じdata容量16B・line幅4Bの4行を1-way/2-wayへ分けたときの配置と置換を比較する。metadata容量は比較容量に含めない。共有元と既受入教材はread-only。これは実装前に固定する有限模型の契約であり、実施状況はstatus.jsonで別管理する。

## 固定した条件

- memoryは256Bの合成・読専用。byte(a)=(17*a+3)%256。readは1byteを返す。
- アドレスは0..255の整数（bool不可）。各traceは16read以下。全入力をread前に検査する。今回の実験は下記5本で、任意入力拒否の網羅試験ではない。
- 各trace/各方式は独立cold start。全line invalid、tag/blockなし、data空、setごとのrecency列空。
- directは4set×1way、2-wayは2set×2way。合計4行。block=a//4、offset=a%4、set=block%set_count、tag=block//set_count。
- indexで1setを選び、そのset内のvalid+tag一致をway番号昇順で探す。hitはそのway、missは最小invalid wayを先に使う。全way validならLRUのwayをvictimにする。victimは置換前のblockであり、新blockや新tagではない。
- setごとにvalid wayだけをLRU→MRUの順で保存。通常はhit/fillとも選択wayを列から外して末尾へ移す。別setの順序は変えない。way番号そのものは位置であって新しさではない。
- missだけblock先頭から4byte全取得、hitは取得0B。返却は選択lineのoffset byte。write/dirty/flushはない。

## 有限の5traceと1故障比較

| ID | byte address列 | 問い |
|---|---|---|
| conflict | 0,16,0,16 | 前作の同index競合を、同容量2-wayなら保持できるか |
| overfull-set | 0,8,16,0,8 | 2-wayの同setへ3blockが来たら、directより良いとは限るか |
| hit-recency | 0,8,0,16,0,8 | hitで更新する新しさがvictimにどう効くか |
| offsets | 3,0,4,7,255,252 | block内の再訪、line境界、アドレス上端でもbyteが正しいか |
| empty | 空列 | 正常なread 0と入力拒否/失敗は同じか |

5本×正常2方式を比較する。hit-recencyだけ、2-wayの「hit時のrecency更新を省略」した意図故障を追加する（合計11結果、48read）。故障でもvalid/tagを調べ、miss fill時はMRUへ移す。byteは正しいが、宣言したLRU規則とvictimが違う。この方式を正しいLRU、任意FIFOの証明、実行エラーとは呼ばない。正常終了した設計反例として記録する。

## 保存する状態と数え方

各readでaddress/block/set/tag/offset、全wayのbefore/after、全setのrecency before/after、hit、選択way、victim block、fillしたblock範囲、返却byte、取得byteを保存する。invalid lineは`{valid:false,block:null,tag:null,bytes:[]}`。read通番は1から、初期状態は別に保存。snapshotはdeepcopyとし、後の置換で過去を変えない。

summaryはreads、hits、misses、evictions（valid victimを置換した回数）、fetched_bytes（miss×4）、hit_rate（空列ではnull）。read数=hit+miss。rate 0と未定義は別。4Bのfillを4missと数えず、offset再訪を新block扱いしない。故障でも返却dataが正しいことと、LRU規則の正しさを別に確認する。

作者手表と独立手表はproducerを読む前に固定する。方式ごとの各readのset/way/victim・recency・選択setのblock列・返却/取得byteを手で追う。保存検証では手表と元memoryの別recurrenceを使い、未選択setが不変であること、全valid lineのblock/tag/data、全snapshotも照合する。producerはexpectedを読まない。

## 実行と受入の境界

Python stdlib 1子、固定11結果を逐次出力する1batch。対象の起動は独立手表・コードreview後、rootのfresh余力確認・単独枠・nice実値10以上・wall約5秒・有限回収が揃ったときだけ。作者は資源guardを新作せず、正確command/入力hash/出力先をrootへ渡す。自動retry0、未開始・失敗・成功を分け、失敗を期待へ合わせない。

GUIはroot提供の既存pageだけを操作するchecker body。作者からbrowser/context/page/serverを作らない。保存readerの予想→操作→原典/実装→答え→限界、前後/条件/予想/reset、取得失敗/復旧、1280/390 viewport、資料本文とdownloadを有限に確認する。実施前は未実施と表示する。

全traceで2-wayが優れるという定理、他容量/line幅/way数/置換方針、write/dirty、実CPU/PMU、latency/energy/一般性能、coherence、完全な3C分類、学習者や一般Agentの能力は保証しない。set数も4→2に変わるため、単に既存setへ空きwayを追加した比較ではない。
