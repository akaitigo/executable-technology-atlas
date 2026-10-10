# 実fileと独立byte oracle

9条件を専有tmpでfixture write→実apply→再read。setup/apply書込数、conflictfields、before/after exactbytes/hash、入力、UTC/runtime、実NotADirectoryError/errnoを原票へ保存。16のbefore/after fileはclosed artifact。checkerはmerge関数を使わずliteral bytesと再readで照合。未知field/version/owner/path等8拒否、6改変拒否。通常検査は専用tmp以外へ書かず、全module file sha256/mtime前後一致をproofへ最後に保存する。

実IABで9条件、全予想4値への単独変更（成功比較→答えを開く→変更）、scenario/local/pathreset、可変localのactual答え、拒否/実書込失敗時の正常答え解除、旧応答非採用、5source導線を確認する。captureは実tool画像、保存不可はsaved=false/path/hash=null。所有tmp/server/tabのみ終了。限定Skill検査は利用者理解度や独立Agent評価ではない。
