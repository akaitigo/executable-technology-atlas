# 実行前のliteral期待と安全境界

所有fileのbytesはAAAA（4byte）、mapping length4/offset0。index1のAへbyte66（B）を書込む。shared/private/read-onlyは各別tempfile、同一process内で副ACCESS_READ mappingとfresh file readを使う。

| mode | write | mapping | 副readonly mapping | fresh file read / close後 |
|---|---|---|---|---|
| ACCESS_WRITE | 成功 | ABAA | ABAA | ABAA |
| ACCESS_COPY | 成功 | ABAA | AAAA | AAAA |
| ACCESS_READ | TypeError拒否 | AAAA | AAAA | AAAA |

期待は[oracle.json](oracle.json)にliteralで固定。producerをimportせずlookupする。sharedのflush前可視性は同一processの別mapping/file readで観測する。flush結果はbytes期待と別欄で記録し、成功をdurability証明にしない。ACCESS_COPYをsharedと同じfile変更と誤解すること、readonlyが書込を許すと誤解することを反例として拒否する。

安全なPython API境界はoffset1/length1のunaligned mmap（OSError）、offset0/length5のfile超過（ValueError）、有効length4 mappingのindex4 read（IndexError）、close後index0 read（ValueError）。実errno/messageはrawに記録し、message全文をportableな契約としない。fileはmapped中にtruncate/resizeせず、ctypes/pointer/address操作、実SIGBUS/SIGSEGV、pagefault注入はしない。拒否は実API例外で確認し、signalを誘発する試験ではない。

mapping.closeと元file.closeは別event。mapping.close直後もfile objectはopenという期待を記録する。final cleanupは所有mapping→副mapping→file→tempの順で回収。跨process共有、copy page数、kernel内部、real power lossは未観測。
