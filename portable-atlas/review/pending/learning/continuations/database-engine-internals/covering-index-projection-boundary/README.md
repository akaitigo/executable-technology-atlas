# 出力列を増やすとcoveringはどう変わるか

実Mac Python sqlite3の専用:memory:DBに固定256行と(bucket,label)indexを作り、同じbucket条件のSELECT bucket,labelとSELECT bucket,label,payloadを比べる。indexの存在だけで全出力がcoveringとは判断しない。

```sh
python3 -B server.py --port 0
python3 -B runner.py
python3 -B route.py baseline
python3 -B checker.py
```

予想→操作→比較→原典/実装→答え: server表示URLを開き、coveringと結果列の予想を書く。ケースまたはbucket/projection/orderを変更し、両SQLを実SQLiteで実行。projection切替は注目する結果を変える。NULL、重複、順序を含む全結果とraw4列EQPを見て、模式図・schema・index_xinfoを照合し、原典と実装へ戻る。予想/入力/ケース/resetで旧結果を消し、編集後の保留旧応答を無視する。

[契約](EXPECTATIONS.md)、[256行](rows.json)、[手表](hand-table.json)、[独立filter oracle](oracle.py)、[独立SQLite再照合](sqlite_audit.py)、[原典](SOURCES.md)、[Skill](skills/atlas-covering-projection/SKILL.md)。各rowのNULLと同じ投影値の重複を保持。ORDER BY label,idは同値labelの順序を定め、idはSELECT出力に入れない。index_xinfoのrowid auxiliary列を確認する。

入力はbucket（整数0〜7/99またはnull）、projection=index/payload、order=asc/descの3fieldだけ。bool/任意SQL/path/追加fieldは操作前拒否。各回のDBは:memory:で、file DBや外部接続を作らない。通常CLI/checker/routeは候補をread-only、実測DBを毎回closeする。原票更新は明示runner.py --recordのみ、古い証拠を削除しない。

schema_cover_possibleはindexに必要出力があるか、plan_classは実EQPの有限text matcherによる観測。異なる/未認識planはCOMPARISON_NOT_ESTABLISHEDで表示する。全SQLite版に固定planを強制しない。独立SQLite監査は同じ実行環境でSQL/結果/plan/schema/版/compileoptionsを照合し、原典の一般保証とは分ける。

模式図は採用planの説明で、実B-tree/page captureではない。EQPから速度やページ訪問数は算出しない。空結果でもplanのcovering表示は出力行数とは別。WAL/snapshot/upgrade/単一index式比較、backend README N4、全DB分野の完了は対象外。Subjectの学習文書は参照でruntime依存なし。global gate/公開は未実行。
