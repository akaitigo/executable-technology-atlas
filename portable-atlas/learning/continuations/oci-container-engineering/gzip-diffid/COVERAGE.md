# Atlas｜gzipとDiffIDで今回分かること

今回の範囲は自己所有2048byte tar、gzip mtime0/1、11固定条件です。圧縮descriptorのsize/digestと、非圧縮tar全byteのDiffIDを別々に検査します。改変、metadata自己整合だが元DiffID不一致、cap2047、末尾欠落/CRC/余剰/連結、2種類のdigestを混同する故障を扱います。

11条件のPython実計算と保存結果の独立照合を実施しました。作者308確認・6改変拒否と独立348関係・7改変拒否は別の記録で、合算しません。[状態](qa/reader-acceptance.json)へ。11条件の実DOM、予想/条件/reset、取得失敗と旧応答、1280/390pxの代表3画像を確認済みです。独立の表示照合は207関係。関連3資料のhrefからの移動と本文は照合済みで、リンクの実クリックは未確認です。旧[非圧縮tar](related.html?topic=oci-base)と[opaque whiteout](related.html?topic=opaque)は前提であり、再制作しません。作者の新教材加算は0、元repoへ未統合です。

単一memberだけを受け付けるのは本教材のsubsetです。RFC1952が認めるmember連結の一般的な有効性を否定しません。output cap+1は上限超過を検出するための限定診断で、拒否時に成功payloadとして返しません。

残る範囲：zstd、任意gzip header/複数member、tar formatの一般適合、全入力境界、tarのpath/link/device/permission検証とhost適用、registry、manifest/config連鎖全体、署名・発行者信頼、実container/runtime、圧縮性能・悪意あるarchive一般の資源安全性。schemaや入力4096 byte等のguardは実装されていますが、11条件で全端点を実測したわけではありません。

状態文の修正箇所と最終独立受入は[確認状態](qa/reader-acceptance.json)から辿れます。[元学習経路](related.html?topic=learning-path)のmultiarch選択やtar metadataによるidentity差は次の候補ですが、現在の既存成果を再照合してから選定します。この単元で追加実装は開始しません。
