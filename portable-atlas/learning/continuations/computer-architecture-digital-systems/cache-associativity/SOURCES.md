# Atlas：配置と置換の原典

[Cornell CS3410 Fall 2025 / Caches](https://www.cs.cornell.edu/courses/cs3410/2025fa/notes/caches.html)の著者本文を2026-10-07 UTCに読みました。既存教材の参照先を再利用し、小さい本文だけを読みました。第三者の本文・図・コードはコピーせず、可変Webページを固定commitと扱いません。

- Direct-Mapped Cache / Filling the Cache / Larger Blocks：valid/tag照合、line単位fill、offsetでのbyte選択。今回のdirectは4set×1wayです。
- Set-Associative Cache：set内のwayを調べる構造と、同じ行数でwaysを増やすとset数が減る関係。今回は4行を2set×2wayへ分けます。
- Replacement Policies：LRUは最後に参照した順序でvictimを選びます。hitも参照なので更新します。

容量16B/line4B・合成byte式・5trace・invalid最小way・LRU way配列の具体表現は本教材の固定仕様です。原典の例をそのまま実行した結果ではありません。2-wayの優位性や実時間は原典の説明から一般保証へ広げず、今回の有限反例で比較します。出所pathと読取locatorはrecords/source-read.jsonへ。
