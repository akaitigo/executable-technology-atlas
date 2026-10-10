# IAB再採取の手順

1. checkerを実行して固定fixture/oracle/contractを確認。server起動、専用tabでprobe.htmlを開く。native AX表示とexact role/name queryを別々に保存。API docsにdescription getterがなければUNOBSERVED。DOMから補完しない。
2. indexの条件を12個順に選択。名前予想を見える文字にして誤予想も残す。fresh native AX全文、specimenに限定したDOM snapshot、exact期待name queryと対立候補queryのcountを採取。対象buttonを実clickし操作回数を記録。
3. description値はnull/status UNOBSERVED。observations.jsonは明示採取時のみ書く。source SHAとUTCを付ける。通常UIやcheckerは書かない。
4. 保存比較UIを12条件で再操作。入力編集、条件初期化、503、古い保留応答を確認。原典/source/raw viewerの本文を確認してnative screenshotを保存。
5. read-only CLI前後のSHA・mtimeを比較し、専用tab/serverのみ終了。Browser版未観測を保持し、同じ版の追試とは呼ばない。

採取に使ったAPIと結果はevidence/capability.json / observations.json / browser.json。実ATは起動しない。AX未観測を想像で埋めない。
