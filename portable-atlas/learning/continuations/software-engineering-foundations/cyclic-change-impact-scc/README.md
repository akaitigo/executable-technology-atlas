# 循環を含む変更影響をSCCで解析する

元SubjectのDAG限定解析は循環を拒否しました。この続編は循環を含む宣言graphを受け入れ、SCC（強連結成分）へ縮約してから逆到達影響を有限に計算します。price↔invoice、report→invoice、独立auditの4nodeです。矢印はcaller→dependencyで、依存先の変更は利用側へ伝わります。

前提は依存方向、到達性、test選択。予想→条件選択→実Python解析→比較→一次資料/source/raw→答えの順に進みます。入力順序が変わってもSCC集合と影響集合は変わりません。traceの訪問順とindexは変わり得るため不変とは主張しません。

| ケース | SCC数 | 影響module | 選択test | 故障の漏れ |
| --- | --- | --- | --- | --- |
| cycle-price / order-reversed | 3 | invoice, price, report | 3 | なし |
| bad-cycle | 3 | invoice, price, report | 1 | invoice, price |
| self-loop | 4 | invoice, price, report | 3 | なし |
| bad-self-loop | 4 | invoice, price, report | 2 | price |
| disconnected-audit | 3 | audit | 1 | なし |
| report-only | 3 | report | 1 | なし |

price/invoiceを一つにまとめると縮約DAGのedgeはreport→invoice+priceだけです。変更priceのcomponentからedgeを逆に辿り、reportまで影響します。auditは独立のため不要です。self-loopではsingletonも循環ですが、無影響にはなりません。

故障版drop-cyclicは正しい影響traceを残しながら、循環SCCに属するmoduleをtest選択から取り除きます。先に固定した反例で2件または1件を落とし、BAD_SELECTIONになります。「visitedで既訪問の探索を止める」正常処理と、「循環moduleを選択から除く」故障を区別します。無限再帰は実行しません。

[calculate.py](calculate.py)はTarjanのindex/lowlink/active stackからSCCを作り、component間edgeだけを残し、変更componentの逆到達を求めます。各選択testはmoduleごと1回、selected_test_countsで確認します。ここでtestとは選択識別子であり、製品testを実行した成功証拠ではありません。

[事前literal表](hand-oracle.json)は初回producer実行前に作成。[oracle.py](oracle.py)は各始点から全simple pathを別計算し、相互到達を同一componentの条件に使います。Tarjan/lowlink/producerを共有しません。[check.py](check.py)はliteral集合・独立SCC/影響・縮約edge・sink除去によるDAG性・選択1回を照合します。SCC分裂、循環影響除外、test重複、独立audit混入、未知node許可、故障の漏れ隠蔽の6mutantを拒否します。未知変更nodeと未知edge nodeはINPUT_REJECTEDで、空集合を正常な影響ゼロとは解釈しません。

[Princeton TarjanSCC](https://algs4.cs.princeton.edu/code/javadoc/edu/princeton/cs/algs4/TarjanSCC.html)は強連結componentの識別とTarjan算法の一次資料です。公式Java実装は実行せず、Pythonの有限モデルを実行しました。Section4.2のHTML取得は403で、確認済み資料として採用しません。[source対応](sources.json)に記録しています。

~~~sh
python3 -B check.py
python3 -B route.py cyclic-change-impact-scc
python3 -B route.py unsupported
~~~

最後はexit2で無変更。通常再読はread-only。新しい原票が必要な場合だけpython3 -B runner.py --recordで新UTCディレクトリを作成します。python3 -B server.pyは専有127.0.0.1動的portを表示し、終了はそのプロセスのCtrl-Cです。

[原票](observations/20261005T161335600443Z/raw.json)はUTC/runtime/fixture/source hash/result/探索traceを保持します。[画面観測](observations/iab.json)、[合成失敗](observations/failure-qa.json)、[実遅延応答の破棄](observations/held-qa.json)、[cleanup](observations/cleanup.json)、[検証receipt](observations/verification.json)を参照できます。captureはツール表示で確認しましたが、保存fileはありません。

各予測変更は新値と他予測を保持し、旧答え本文を空にして閉じ、比較/trace/rawを未実行に戻します。条件変更は全予測unknown。合成return failureとHTTP503はEXECUTION_FAILURE、oracle未判定であり、subset拒否と別です。generation変更後の保留した実応答を返しても旧答えは復活しません。

固定4node・9fixtureのsyntheticモデルで、stdlibのみ。任意graph入力、実repo依存抽出、動的import、未記載依存、製品test実行、要求coverage、設計品質保証は未実証です。次候補は実repo宣言依存と抽出依存の差分、要求/test bindingの変更で、未制作です。元Subject、既存教材、Portal/Core/fullGate、OS設定、install/commit/pushは対象外。分野/Atlas全体の完了は未主張です。
