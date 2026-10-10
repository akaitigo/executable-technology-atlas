# Atlas：原典・既存実装・今回の比較

[sources.json](sources.json) は必要な元ファイルの場所・hash・読む箇所を示す。ファイルの存在やhash一致だけで意味の読了を主張しない。今回の読取では既存の分散/Edgeの実装、保存結果、対応するcheckerを確認し、新しい対象計算は行っていない。

| 一次資料の箇所 | 確認した規則 | 今回の対応 |
|---|---|---|
| Lamport (1978), 刊行p.559, The Partial Ordering | 同一process順序、同一messageのsend→receive、推移性 | 入力の6辺、全15組、経路の証拠 |
| 同p.560, Clock Condition / IR1・IR2 | 因果があれば時計値が増える。逆は要求しない | 固定時計の条件照合、逆推論の2偽陽性 |
| 同pp.560–561, Ordering the Events Totally | 全順序への拡張は一意でなく、部分順序と異なる | 2つの合法再生順、表示辺混入の4偽陽性 |

[著者公開PDF](https://lamport.azurewebsites.net/pubs/time-clocks.pdf)を2026-10-06に本文取得して読んだ。本文全文や図は同梱しない。Web取得本文のbyte hashは採取しておらず、元ローカルファイルのhashと混同しない。画面の資料導線で外部通信を遮断する場合、クリック到達と公式本文の読取は別に記録する。

今回の模型が原典から追加したものは、6イベントの合成入力と2種類の誤推論比較である。物理時間、実送受信、論文の相互排他algorithmは実装しない。

R1/R2は因果の辺を保つ表示用の順序で、今回の固定時計を昇順にしてtie-breakしたLamport全順序ではない。R1のb2→d1、R2のf3→b2という表示上の減少も合法である。

Edge教材のversion vectorにはDynamo §4.4 Data Versioningへの既存対応がある。今回その計算を再実行せず、元の保存結果とコードを前提確認に使う。新しい全event vector clock実装の根拠として転用しない。
