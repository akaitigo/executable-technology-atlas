# SQL第2単元 — window frameとpeer

元入口の [README](../../../subjects/relational-database-sql/README.md) と [LEARNING_PATH実験2](../../../subjects/relational-database-sql/LEARNING_PATH.md) から続く独立教材。元moduleのREADME・原票・QA・binding・Skillは変更しない。このcontinuationの追加は分野受入数の追加でも、SQL分野全体の完成でもない。

前提は行ID、partition、sort key、NULL、SUM、ORDER BY。「選ぶ行 → partitionと順序 → frameのID集合 → known amount → sum → 実SQL/原典 → 答え」を [index.html](index.html) で操作する。保存SQLiteの12ケース・33 statementを実行し、各行のframe集合/累積値を記録する。UIは保存観測readerで、操作によるSQL再実行はしない。

default RANGEは `SUM(amount) OVER (PARTITION BY part ORDER BY sort_key)`。既定はunbounded precedingからcurrent rowを含むpeerまで。ROWSは `ORDER BY sort_key,id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` で、idがuniqueなので1行ずつ進める。この2つはORDER BY契約も異なる。ROWSをsort_keyだけで実行した結果のpeer順序を保証したとは扱わない。

peer表Aにはid1=(key1,10)、id2=(key1,20)、id3=(key2,5)。default RANGEのid1/id2はframe {1,2}で30、ROWSのid1は{1}で10、id2は{1,2}で30。id3は両方{1,2,3}で35。partition Bのid4=(key1,7)、id5=(key2,NULL)はAと混ざらず累積7。INSERT順を3,2,1,5,4としてもROWSはsort_key,idで決める。

明示RANGE sort_key-onlyも記録してdefaultと比較する。追加caseではRANGEをsort_key,idにするとunique idがpeerを分け、ROWSと同じframeになる。frame名だけで結果を判断せず、partition/order/boundsをセットで読む。

境界はNULL sort peer（ASCで先頭）、all-NULL amount（SUM=NULL、COUNT(amount)=0）、negative amount、negative key、同順位なし、singleton、NULL partition key、存在しないpartitionのfilter、invalid reversed/negative frame。空partitionのwindow結果は0行であり、SUM=0の1行ではない。all-NULL frameは行とframeが存在しSUM=NULLになる。invalid frameは実OperationalErrorを保存し成功へ変換しない。

各SQLはSUM/COUNT/GROUP_CONCAT(id)を同じwindowで実行する。GROUP_CONCATのraw文字列順はpeerのID集合順を保証しないため、集合としてsorted IDsへ正規化する。outer ORDER BY part,sort_key,idは画面の結果順でありwindow orderとは別。NULLはIS的なpeer等価性を持つこの有限fixtureで検算し、全dialect/型/collationの一般化はしない。

[checker.py](checker.py) は保存DBからinput列をSELECTするだけで、SUM/window SQLを再実行しない。partition内のPython順序と集合列挙からframeを作り、NULLを除いた整数を手集計する。さらに11個のliteral frame/sum anchorを併用する。SQL raw rows/columns、ID集合、known値数、sum、順序、error、DB digestとquery_only=1を照合する。

```sh
python3 runner.py                         # 既存証拠のread-only確認
python3 checker.py
python3 test_negative.py                  # disposable copy改竄5種 + read-only確認
python3 runner.py --record                # 明示的な原票更新時だけDB生成/SQL観測
python3 preview.py                        # 一時loopback、確認後Ctrl-C
python3 skills/atlas-sql-window-frames-peers/route.py window-peers
```

[current.json](current.json) からUTC時刻/Python/SQLite/OS、fixture.sqlite3、作成SQLとinput順、実SQL/params/columns/raw rows/order/frame IDs、raw command/trace、source/artifact SHA256へ到達する。observe.pyとcheckerは `mode=ro&immutable=1` とquery_onlyで読む。接続は明示closeし、DB hashの不変を確認。[qa.json](qa.json)・[verification.json](verification.json)・[ui-observations.json](ui-observations.json) に実画面QAを保存する。

実務で増えた判断は、同sort keyをまとめる計算と1行ずつ進める計算の選択、peerとtotal orderの区別、NULL sumと空結果の区別、集計値だけでなくframeの行集合を確かめること。数値型は小さい整数とNULLに限定し、overflow/浮動誤差・製品間dialect・性能・transaction安全性を検証しない。

新しく追加したcoverageはwindow/partition/frame/peerのこの有限範囲。未教材はbounded RANGE/GROUPS/EXCLUDE、DESC/collation/mixed type、ranking/navigation/FILTER、GROUP BY/HAVING/JOIN分母、transaction/locks/migration、正規化/planner/CTE/backup/権限。元の実験1・3・4は元moduleの案として残る。[coverage.json](coverage.json) に今回から続く具体的な問いと次の4実験・locatorを保存する。

一次資料は [SQLite Window Functions](https://www.sqlite.org/windowfunctions.html) §2.1/§2.2（default frame/peer/ROWS/RANGE/bounds）、[SELECT](https://www.sqlite.org/lang_select.html) のORDER BY/NULL、[Aggregate Functions](https://www.sqlite.org/lang_aggfunc.html) のsum/count/group_concat、[Python sqlite3](https://docs.python.org/3/library/sqlite3.html) のURI read-only。[sources.json](sources.json) に確認日/locatorを保存し、実runtime版は原票に記録する。外部DB・旧PG・旧Goal・root gate・公開/commit/pushを扱わない。
