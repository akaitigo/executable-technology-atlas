# 実装前の有限契約

容量枝 R-CAP→D-CAP→T-CAP とFIFO枝 R-FIFO→D-FIFO→T-FIFO。各1要求/設計/testの独自6node。変更内容は容量3→2を想定するだけでqueue動作を実行しない。到達集合は起点自身を含む。要求変更forwardとtestからreverseは別の問い。

forward/reverseは独立保存し、自動生成・欠落修復しない。reverseのD-CAP→R-CAPを1本だけ消す。正常の容量forward/reverseは{R-CAP,D-CAP,T-CAP}、FIFOは{R-FIFO,D-FIFO,T-FIFO}。欠落時forward容量は3ID、reverse容量は{T-CAP,D-CAP}。どちらもTRACE_INCOMPLETEであり『影響なし』・完全traceを出さない。残りの枝のgraph到達に外挿しない。

手書き[到達集合と逆link対応表](oracle.json)をproducer実行前に固定。別の隣接行列閉包はforward/reverseそれぞれのgraphで全到達を計算し、対応表は欠落を独立検査。producer traversalはDFS。

構造の必須field nodes/forward/reverse。field型list、6nodeの固定ID/type/text、重複ID不可、edgeは長さ2のstring list、重複edge不可、endpoint既知、forwardはrequirement→design/design→test、reverseはtest→design/design→requirement、同枝だけ。方向forward/reverse、start既知かつforward要求/reverse test。field欠落/型不正/未知ID/edge型不正等はINPUT_REFUSED。存在する空edge listは欠落関係としてTRACE_INCOMPLETE（正常とは扱わない）。この許容型は一般graph入力の仕様ではない。

優先順位: field/型→node→edge→方向→start→対応不足→探索。実Error注入は実RuntimeErrorを捕捉してEXECUTION_FAILURE、到達結果/正常答えなし。未知caseはINPUT_REFUSED。起点だけの到達でもtrace不完全を『影響なし』に変換しない。

UIは条件変更で2予想・旧raw/比較/答えを消す。各予想の単独input/changeは新値と他予想を保持し旧raw/比較/答えを消す。入力拒否も予想と理由を比較する。実行失敗は正常答えを隠す。通常runner/checker/routeは証拠を更新しない。明示--recordだけ新receiptを追加、旧raw保持。unexpected失敗はcurrentへ昇格しない。
