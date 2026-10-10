# HTTP実行前の有限契約

固定route `/orders`、method POSTのみ。Content-Typeは厳密`application/json`、Content-Lengthは必須ASCII十進数字、1..128 byte（0は400、129以上413）。Transfer-Encoding指定は拒否し、chunked処理をしない。宣言より短いbodyの実socket実験は未実施で、clientは既知長bodyだけを送る。oversize/missing/bad lengthはread前に拒否し、DB接続を取らない。

UTF-8 JSON objectでkeyはunitsだけ。boolを除くinteger1..3を許容。invalid JSON400、入力型/範囲/余分key400。HTTP status/body mappingは教材独自で、PEP3333がこのmappingを要求するわけではない。

normal-jsonは201/body order_id1 amount200、orders1/outbox1、取得1/close1。invalid-jsonは400/body invalid JSON、両表0、request取得0/close0。第二SQL故障は500/body storage failure、両表0、取得1/close1。次のnormal requestは同じDB・新接続で201、両表1、取得1/close1。その他のliteral応答は[手書きoracle](oracle.json)。正常専用DB、拒否専用DB、故障→復旧専用DBの3groupで初期状態を分離。

故障は第一INSERTの後、第二SQLだけを存在しない`missing_outbox`へのINSERTに置換。SQLite OperationalErrorを実発生させる。rollback→connection close→closed SELECTがProgrammingError→start_responseという順を予測。SQL traceとread-only SELECT snapshotを別の証拠として保存する。同transaction outboxの知識を再びcoverageに数えず、今回はHTTP transportとrequest所有resourceの境界を学ぶ。

wsgi.input/errorsはserver所有なのでappはcloseしない。bodyはCONTENT_LENGTH以内のread(size)、応答はbytes iterable、start_responseへstatusとheadersを渡す。serverがHTTPclientへ送ったstatus/bodyと独立SQLを照合する。bodyを返した後のfailure、framework DI、auth/TLS、concurrency/負荷は未実験。
