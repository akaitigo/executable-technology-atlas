# 先固定した契約

実Mac標準Python sqlite3の専用:memory:DBでrows.jsonの固定256行を使う。schemaはsamples(id INTEGER PRIMARY KEY,bucket INTEGER,label TEXT COLLATE BINARY,payload TEXT)、index samples_bucket_label_idx ON samples(bucket,label)。payloadもNULLを許す。rowsのidは1〜256、bucketは0〜7/NULL、labelはL0〜L4/NULL。重複する出力行を消さない。

入力は厳密にbucket/projection/orderの3field。bucketは整数0〜7/99（empty条件）またはnull、bool拒否。projectionはindex/payload、orderはasc/desc。任意SQL/path/追加field拒否。毎回両projectionを同じ条件で実行し、projectionは画面で注目する結果を選ぶ。SELECT bucket,label と SELECT bucket,label,payloadを比較。NULL bucketはWHERE bucket IS NULL、整数はWHERE bucket = ?。ORDER BY label ASC,id ASCまたはDESC,DESC。ASCではlabel NULLが先頭、DESCは末尾。idは同値labelの順序だけを決め、SELECT出力には加えない。implicit rowidはindex_xinfoで確認する。

rows、手書きliteral行、bucket0/NULL/99の順序id表をproducer前に固定。独立Python filter oracleはSQLやproducer helpersを呼ばずNULL-aware filter/sort/projectionで全結果を照合。結果の列数・NULL・重複・順序を別に確認する。

実sqlite_version/source_id、Python版、compile_options、schema、table_info、index_list/index_xinfo、loaded rows、raw4列EQP、SQL/binds、全結果、cursor.descriptionを保存。plan detailはruntime依存。有限text matcherでCOVERING_REPORTED/INDEX_TABLE_LOOKUP_REPORTED/OTHER_OR_UNRECOGNIZEDを表示する。schemaでcover可能かと採用planを分け、index存在だけでpayload出力もcoveringと主張しない。index-onlyがCOVERING、payloadが通常indexの対照を観測しなければCOMPARISON_NOT_ESTABLISHEDを残す。特定detail文字列/全SQLite版のplanを成功条件にしない。EQPから速度・ページ訪問数を計算しない。

producer --failはDB作成後RuntimeErrorをEXECUTION_FAILED exit3としてcleanup保持。不正入力はDB操作前INPUT_REFUSED exit2/db_opened=false、正常exit0。finally closeの後SELECTを実呼出してProgrammingErrorを確認し専用DBを回収する。

原典EQP§1.1/出力形式注意、Query Planning§1.6〜1.7。模式図はschema/採用plan解釈を描く説明図で物理page captureではない。WAL/snapshot/upgrade/単一index式比較/backend README N4/全DB分野完了/実性能は対象外。
