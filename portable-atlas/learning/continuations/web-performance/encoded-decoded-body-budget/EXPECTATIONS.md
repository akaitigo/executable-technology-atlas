# 実HTTP producer前の固定期待

plain ASCIIabcはhex616263、3 bytes。gzipはhex1f8b08000000000000034b4c4a0600c241243503000000、23 bytes。gzip decodeはabc/3 bytes。任意gzip生成器の結果を期待値にせず、この固定bytesだけを配信する。

[独立literal表](oracle.json): encoded budget8はplain受入/gzip拒否。decoded3流用故障はgzipを誤受入。gzip23受入/22拒否、plain3受入/2拒否、budget0は拒否。budgetは0..23整数、bool不可。encoding plain/gzip、policy encoded/decoded-fault、余分keyや未知variantは拒否。

Python http.clientは実loopback responseの生bytes/headerを採取してgzip.decompressでdecodeする。HTTP body bytesとそのdecodeを独立literalに照合する。Browserは同origin実fetch、unique URL/no-storeでarrayBufferを読む。これはbrowserでdecode済のbody。実ResourceTimingのencodedBodySize/decodedBodySizeを取得し、HTTP原票の独立長へ結合する。lengthをheaderやモデル値で埋めない。missing entry、非数値、0等の固定bodyと不整合はunsupported/failureで、受入成功にしない。

16case: 9正常/故障policy、5入力拒否、注入timing欠測、実HTTP500。欠測注入は実fetch後に誤lookup keyを使いentryなしを作るもので、Browser API本来の欠測を測定したとは呼ばない。HTTP500は実serverの意図error経路。PythonはResourceTimingを実行できないので欠測caseをBrowser確認必須として区別する。

全3入力（2予想/条件JSON上書き）は成功→答えを開く→一欄変更を最初から実IAB確認、新値/他欄保持、旧測定/raw/答え本文空・閉鎖。condition resetは予想/JSONも消す。答えは現inputのbudget/policyと実測値に追従し、拒否・欠測・実Errorは正常答えなし。受信済実HTTP資料の描画保留で旧versionを破棄、sleepや通信遅延実証なし。

wire総bytes、header/TLS/TCP overhead、latency、cache/CDN、cross-origin、一般圧縮率、WebVitals全般、全Subjectの完成は未実証。通常checker/routeはread-only、runnerのliveは自分の稼働server portを明示、原票保存は明示 --recordのみ。旧rawは保持。
