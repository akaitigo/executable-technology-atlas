# Atlas — CDC事象転送の範囲

目標10の次の一歩は2クロックのpulse/level/toggleと失う事象です。既存counterの同時更新、ready-validのstall中保持・捕捉は前提として差し引きます。既存183件の再実装・再計算は行いません。

| 対象 | 今回の固定比較 | ここから保証しないこと |
|---|---|---|
| 短pulse | [2,4)をdestが取り逃がす | すべてのpulse幅・位相・周波数比 |
| 保持level | [2,10)を複数回sample、立上り1回 | 任意のevent列をlevelで一意に数えること |
| toggle | 1事象と間隔12の2事象を検出 | 製品の最小gapや一般的速度限界 |
| 近接toggle | 間隔2の偶数反転を見落とす | 宛先が未観測数や元のevent IDを知ること |
| 2FFとhistory | 旧値から同時更新する理想論理 | metastability・MTBF・setup/holdの物理量 |

契約と手時系列を先に固定します。固定5条件の計算と保存値の独立照合は完了しました。100時点の実画面操作と9画像の個別目視も完了し、現在の状況は [確認状態](qa/reader-acceptance.json) に記録します。counter/ready-validの説明済み原理や成功例を新たな成果として加算しません。作者の加算は0です。

実RTL/HDL実行、合成、STA、実FPGA、resetの安全な解除、CDC report、ack/handshake、async FIFO/Gray code、bus転送は未対応です。実務では事象とlevelの意味、許す発生間隔、受信側の捕捉条件、未観測時の対処を別々に決める必要があります。
