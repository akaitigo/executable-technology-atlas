# CSV reader版と列の意味

実CSVをPython stdlib DictWriter/StringIOで生成し、DictReaderで名前からtyped fieldへ読む。独自契約のv1/v2 readerを2×2で比較する。旧readerはnoteを未知列として拒否、新readerはnote列がない場合だけ(default)を補う。optional追加が無条件に互換とはいえない。

このディレクトリ内だけの候補。中央の受理reviewとglobal audit/gateは未実施。repository全体のcomplete、RFC CSVやschema標準への適合は主張しない。

## 再現

Python標準ライブラリのみ。通常検査はread-only。

    python3 -B checker.py
    python3 -B runner.py
    python3 -B route.py
    python3 -B qa/check-ui.py
    python3 -B server.py

表示された自分のportで http://127.0.0.1:PORT/ を開く。自身のloopbackだけで実行し、RAM receiptを保存するなら停止前に取得する。Ctrl-Cで自分のserverを終了する。新UTC観測の保存は明示的な runner.py --record だけ。

## 読み方

まず2×2 cellを選び、受入／拒否を予測する。raw CSV、header→field対応、実typed行と拒否位置を比較する。原典と実装を開いてから答えを見る。

reorderedの同型整数2列はquantity=2,unit_price=7。position-faultでは名前を使わず位置0/1/2へ割り当て、quantity=7,unit_price=2へ入れ替わる。parse成功は意味の正しさを保証しない。正常の名前読取と故障対照を同じCSVで切り替えて確認できる。

note列の欠落default、空セルの空文字、列があるのに行のセル数が足りない拒否を区別する。ファイル中で後の行が不正ならtyped_rowsは空とし、途中の解析履歴はcommit済み結果と区別する。

## 原典と独立性

[Python csv公開docs](https://docs.python.org/3/library/csv.html)のDictReader/DictWriter、restkey/restval、line_numを2026-10-06に実読。公開ページは3.14.8、実測runtimeは3.9.6。3.12追加のQUOTE_NOTNULL/QUOTE_STRINGS等は利用していない。標準ライブラリは文字列を読むが、本教材の整数／header policyは独自処理である。

実装はDictReaderの名前mapとregex型検査。oracleはcsv.readerのlistと別の添字／文字集合検査で、producerやhelpersをimportしない。CSV tokenizerというstdlib primitiveは共有するため、完全に独立したCSV parserではない。実装前に固定した14個のliteral token列とend_line、30期待値が共通parserの誤りを見逃すリスクを補う。さらに全known headerの30順列と数値字面22組を照合する。

行番号は物理行、record番号はheaderを除くdata record。quoted newlineの1 recordは物理2行にまたがる。raw表示末尾の空行は最終改行の可視化であり、追加CSV recordではない。

実UIは120予想比較、2×2 cell4、正常／故障切替6、編集10、stale消去4、reset30、3 JPEGと10原典／実装導線を検査する。151 POSTの実receiptをRAMから保存し、列別typed値と照合する。失敗・cleanup・bindingはqaへ残す。
