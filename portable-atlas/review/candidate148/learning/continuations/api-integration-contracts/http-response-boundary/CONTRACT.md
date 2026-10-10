# Atlas：本文の受信完了を先に確かめる

問いは「JSONとして読めるbytesが返り、例外もなかったら、応答を使ってよいか」。HTTP、JSON、本文長と上限を前提に、完全な応答かという検査をJSON解釈の前へ置く。上限やProblem memberの原理を新しく数えない。

## 固定入力

[cases.json](cases.json)の4入力を使う。すべてGET、HTTP/1.1、422、application/problem+json、単一の非負整数Content-Length、Transfer-Encodingなし、Connection: close。基準本文は前作と同じ105byte。上限対照は末尾にASCII spaceを8087/8088個加える。

| ID | 宣言長 | 送信本文長 | 意味 |
| --- | ---: | ---: | --- |
| complete | 105 | 105 | 完全なJSON本文 |
| short-content-length | 106 | 105 | JSONは同じだが、宣言より1byte不足 |
| at-limit | 8192 | 8192 | 同じJSONと空白、上限ちょうど |
| over-limit | 8193 | 8193 | 同じJSONと空白、上限を1byte超える |

short-content-lengthは保存済みの不透明なID。Content-Lengthが小さいのではなく、本文105に対して宣言106である。画面では「宣言106・本文105」と表示する。

## 読取と判断

本文上限8192byte、各responseに **HTTPResponse.read(8193)を1回だけ**。追加read、無制限read、再接続・再試行はしない。status/header、本文の長さ・hex・SHA、read例外、呼出し前後のHTTPResponse.lengthとisclosed()を保存する。length/isclosedは実装版に依存する補助観測で、一般の完了判定には使わない。

case名や期待値を渡さない利用側は次の順に検査する。拒否後は後段not-run、decodedJSON=null。

1. framing：読取例外なし、単一Content-Lengthと受信長が一致。この4入力は最大8193byteに固定しており、任意の巨大応答の全受信を保証しない。
2. budget：受信長が8192以下。診断値withinBudgetと、この段階へ実際に到達したことは区別する。
3. media：固定endpointが期待するapplication/problem+json。一般MIME文法は検証しない。
4. JSON：UTF-8とJSON構文を読み、成功時だけdecodedJSONを返す。2到達入力の結果は同じtype/title/status object。Problem Details全適合や業務成功は認定しない。

outcomeはcomplete/at-limitがjson-ready、short-content-lengthがincomplete-response、over-limitがbody-limit-exceeded。拒否本文も文法上は完全なJSONであることは入力と独立手表から説明し、拒否した利用側がJSON解析を実行したことにはしない。前作consumerは1KiBの別契約なので変更・流用せず、member政策は前提資料へ戻す。

## 実装前の予測と受入

固定CPython v3.9.6の非chunked実装を読んだ予測は、4件のread例外すべてnull、返却長105/105/8192/8193、length残り0/1/0/0、isclosed true/false/true/true。実行時のPython版・実import元path/SHAを別に記録する。不一致でも観測を残し、公式版とのファイル全体の同一性を仮定しない。

「例外なしだけで完了とみなす」という誤った推論を、同じ保存受信の比較欄へ示す。shortだけを誤って完了とみなす予測だが、新しい通信や業務処理は増やさない。正しい完了とこの推論を別値で保存する。

独立担当はproducerをimportせず、実装前のliteral表へ4応答のbytes/宣言長/受信長/段階到達/返却objectを照合する。入力前後、実行版、自己所有資源の終了、欠落・長さ置換・拒否後の残留を少数の保存値改変で確認する。GUIは既存の1ページで予想→保存実測→比較→原典/実装→答え、変更・取得失敗・古い応答時の消去と1280/390px可読性を確認する。reader操作ではHTTP実験を再実行しない。

## 実行条件

既存Mac Python標準ライブラリのみ。rootの単独枠と新しい資源確認後、actual nice>=10を確認した1子で127.0.0.1:0の自己所有HTTPServer1個・thread1個・4逐次GETを実行する。socket timeout2秒と全体wall15秒は停止の境界でありtimeout実測ではない。finallyでresponse/connection/server/threadを閉じる。他のサービス・ブラウザーを操作せず、回収が不明なら成功扱いしない。

現在は未実行。実装・GUI・独立受入を先取りしない。[範囲](COVERAGE.md)と[原典](SOURCES.md)へ戻って判断する。
