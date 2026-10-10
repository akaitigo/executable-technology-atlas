# opaque whiteoutでlowerだけを隠す

[元OCI教材](../../../subjects/oci-container-engineering/README.md)のopaque未対応を、実2layer USTAR bytesと独自有限mapへ進める部分教材。既存Python3.9.6 tarfileがmember bytesを読む。hostへextractせず、Docker、container、overlayfs、permission操作は実行しない。

前提はtar memberとlower/upper。予想→実USTAR読取→member順/正常故障→原典/source/raw→actual答え。画面でd/aのbytes newA/newXとmarker pathを変え、結果mapから作る答えを比較する。

|条件|upper member順|実map|
|---|---|---|
|opaque先|marker, d/a=newA, d/c=newC|d/a新、d/c新、keep=k|
|opaque後|d/a新, d/c新, marker|先と同じ、lower d/b消滅|
|opaqueなし|d/a新, d/c新|lower d/b=oldBも残る|
|逐次適用故障|d/a新, d/c新, marker|keepだけ。同層まで消す誤り|

lowerはd/a=oldA、d/b=oldB、keep=k。empty d/.wh..wh..opqがd/のlower childrenを隠すが、同層のnewA/newCは残る。markerはmapへ表示しない。全memberを検査してからlowerのcopyを作り、opaque処理と同層file適用を分ける。入力lower mapを変更しない。

[OCI Image Spec v1.1.1 Layer Whiteouts / Opaque Whiteout](https://github.com/opencontainers/image-spec/blob/v1.1.1/layer.md#opaque-whiteout)はlowerだけへの適用、marker非表示、opaqueによるchildren/descendantsの隠蔽と順序に依存しない同層file保持を説明する。今回のmapは小さな比較模型で、OCI全適合・実filesystemの実証ではない。

独自subsetはASCII canonical相対path、d/a,d/b,d/c,keepの通常fileとd/のempty opaqueだけ。祖先外/絶対path、非empty opaque、symlink/hardlink、duplicate、directory、普通の明示whiteoutは拒否。明示whiteoutは元教材で扱うが、この単元は対応せず独自subset拒否とする。拒否はfinal map無し、入力lower不変。壊れたtarは実ReadErrorでsubset拒否と分ける。

手表は実装前にliteral member bytes/finalmap/拒否理由を固定。独立oracleはapplierを共有せずliteral最終mapを照合し、tarfileを使わない512byte USTAR header decoderで保存tarのchecksum/name/type/size/bodyを再readする。directory tar headerの末尾slashは拒否fixtureのname照合時だけ除去する。標準hash primitiveとPython runtimeは共通で、別runtimeや全tar parserの検証ではない。

```sh
python3 -B verify.py --record attempt-01  # 未使用attempt、tar26個とraw
python3 -B verify.py --seal-record       # QA後current binding
python3 -B verify.py                     # 実再生成/読取、module保存なし
python3 -B route.py
python3 -B serve.py                      # 動的localhost、終了Ctrl-C
```

13条件（適用4、subset拒否8、実tar失敗1）、改変拒否6種。初回raw/receiptを保全、QA後にcurrent bindingをseal。全可変入力reset、予想だけ変更で新値保持/本文消去/閉鎖、拒否・実失敗に正常答え無し、旧応答非採用を確認する。

未実証: nested opaque、directory属性、permission/owner/xattrs、linksの適用、圧縮tar、descriptor/DiffID chainの追加検証、host展開、実overlayfs/runtime/container、安全性、全OCI適合。次はnested descendants、directory metadata、実runtimeとの比較（未実行）。元Subject・旧unit・Portalは変更しない。install・Docker設定・公開・commit/push・Core gateは範囲外。
