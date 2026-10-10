# Data engineering / orchestration — CSVが公開データになるまで

Python標準ライブラリだけで、固定CSVを ingest → typed transform → batch内dedup → generation作成 → current pointer公開へ通す有限教材。13ケース・18回を実行し、独立した手計算の行・schema・lineage・件数に照合する。科目全体の完成ではない。

前提はCSVのheader/record、文字列と整数、キー、プロセス終了コード。まず [index.html](index.html) で出力行数・終了状態・件数保存を予測し、ケースと試行を操作して比較する。保存済み実行の観測を表示するUIであり、ブラウザ操作によってpipelineは再実行されない。表示された原入力・raw command・trace・lineageから答えへ戻る。

既存 `workflow-batch-orchestration` は純粋な整数taskの依存DAG、状態遷移、bounded retry、cycle拒否を学ぶ。本教材は実際のCSVの型・品質・重複・公開ファイルを扱う。production schedulerやremote ETLはどちらの実行証拠にも含めない。

主要な仕組みは、厳密header、quantity 1..100、priceの小数2桁/0..100000、Decimalから整数cents、同一ID・同一値の重複除去、異なる値の同一IDのquarantine。IDはstrip後に比較する。入力を全件メモリに載せ、最初の有効行を採用しIDで出力sortする。schemaの整数はCSVそのものの型ではなく、sidecar contractとcheckerによるcanonical整数セルの約束である。

通常入力4件は a=(2,125,250)、b=(1,10,10) の2行、同値重複1件、quantity不正1件になる。quarantineでは2+1+1=4。silent skipでは公開lineageとquarantineから不正行が消え2+1+0=3となる。raw observer traceにはskipを残すため、欠落を発見できる。意図的な悪い比較である。

同じbatchのreplace再実行では公開pointerと5ファイルがbyte単位で同じ。append再実行では出力が2→4行になりa,bが重複する。batch内dedupは過去の出力全体に対するdedupを意味しない。append lineageは現在batchの3/4件を記録し過去行を完全に追跡しない。この不足も運用判断の材料になる。

境界は空入力、全件不正、価格0、quantity上限100/超過101、conflicting ID。正常公開後のheader不一致、変換段階失敗、publish直前失敗では前回公開のpointerと各ファイルを保持する。不変generationにoutput/quarantine/schema/lineage/manifestを置き、最後に単一current pointerを同一filesystemでreplaceする。readerはpointerを一度読み、そのgenerationを参照する必要がある。

実務では「成功exit」だけで品質を判断せず、input = accepted + duplicate + quarantined とlineage、再実行の出力範囲を確認する。不正行を止めるか隔離して進むかは業務要件次第。replaceはここでの固定batchのidempotenceであり、他のbatchや外部副作用のexactly-onceを保証しない。

```sh
python3 runner.py                  # defaultは既存証拠のread-only確認
python3 checker.py
python3 test_negative.py           # 一時コピーの改竄4種 + read-only確認、終了時削除
python3 runner.py --record         # 明示的な原本再生成だけ
python3 preview.py                # 動的loopback一時preview、Ctrl-Cで停止
python3 skills/atlas-data-engineering-orchestration/route.py csv-pipeline
```

[current.json](current.json) から実行原本へ到達する。原本はUTC時刻、OS/Python、input、commandのstdin/stdout/stderr/exit、NDJSON trace、各試行後の公開snapshot、実際の不変generation、独立oracle、source/artifact SHA256を含む。[checker.py](checker.py) はproducerをimportせず固定手計算表と物理ファイルを比較する。検証・画面QAは [qa.json](qa.json)、[verification.json](verification.json)、[ui-observations.json](ui-observations.json) に保存する。

未実行・限界: 複数writer、fsync/power loss、kill/OS I/O障害、generation GC、並列/distributed ETL、scheduler、network、remote storage、CDC/backfill、schema evolution、大規模join、event time/watermark、標準PROV出力。失敗注入は明示的なRuntimeErrorであり電源断再現ではない。source hashは改変検知であり署名や第三者の信頼証明ではない。未カバー概念・問い・次の4実験は [coverage.json](coverage.json)。

一次資料: [Python csv](https://docs.python.org/3/library/csv.html) のreader/newline/line_num、[Decimal](https://docs.python.org/3/library/decimal.html) の十進演算、[os.replace](https://docs.python.org/3/library/os.html#os.replace) の置換、[W3C PROV primer](https://www.w3.org/TR/prov-primer/) §2のentity/activity/generation、[Airflow Dags](https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/dags.html)、[Beam Programming Guide](https://beam.apache.org/documentation/programming-guide/) のWindowing/Triggers。[sources.json](sources.json) にlocatorと確認日を保存。後者は科目の未カバー領域を読むための資料で、実行証拠ではない。
