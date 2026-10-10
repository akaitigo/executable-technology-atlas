# この有限単位のCoverage

6 node / canonical4 link / old-new2 snapshot / stored proof最大2。固定22条件、編集4条件。要求revision/content、test実装revision/content、design/link revision、link追加削除、未影響枝、欠落proof、旧proof、FAIL、同hash同revision/同hash新revision、順序対照、schema拒否4、実RuntimeError1。

実IABでは全26条件の表・図・raw/receipt・答えを実子processと照合し、全3入力reset、条件reset、stale二通り、JSON拒否、HTTP503を検査する。別oracleはproducerをimportせず行列閉包、手表/literalと同時照合する。独立は別実装で別の人の要求承認ではない。変異検査・実行数・不変SHA/mtimeの結果はevidence/verification.jsonを正本にする。

分野全体のCoverage率を算出しない。実test再実行、要求妥当性、実製品link完備、承認/validation、循環/性能/Safetyは未実証。
