# Atlas：原典と既存教材への対応

公式本文は2026-10-07にread-onlyで確認した。現在の画面や関数がRFC全体に適合するという認定ではない。

| 読む箇所 | 今回の判断 | 境界 |
|---|---|---|
| [RFC 9457 §3](https://www.rfc-editor.org/rfc/rfc9457.html#section-3) | application/problem+jsonはProblem DetailsのJSON表現 | custom形式も有効な契約であり置換を強制しない |
| [§3.1](https://www.rfc-editor.org/rfc/rfc9457.html#section-3.1) | 型が異なる標準memberを無視 | 今回の実測はstatus文字列の1例 |
| [§3.1.1](https://www.rfc-editor.org/rfc/rfc9457.html#section-3.1.1) | type URIを主識別子とし、自動取得しない | 固定の絶対URIのみ、相対URI解決は未実測 |
| [§3.1.2](https://www.rfc-editor.org/rfc/rfc9457.html#section-3.1.2) | statusはadvisory、生成者は実HTTP応答と同じ値を使う | 伝送と本文の不一致を保留するのは教材consumer方針 |
| [§3.1.3](https://www.rfc-editor.org/rfc/rfc9457.html#section-3.1.3) / [§3.2](https://www.rfc-editor.org/rfc/rfc9457.html#section-3.2) | titleの翻訳は別typeでなく、未知extensionを無視 | traceHintの単例、拡張全般の意味は解釈しない |
| [§5](https://www.rfc-editor.org/rfc/rfc9457.html#section-5) | statusが食い違う場合の相対的優先は明確でなく、intermediary変更もあり得る | 原因を断定せず、実proxy/通信は未観測 |

174受入時点の選定根拠は目標26（目標文書328–335行）、元API README:35とclient.py:12–38。元はapplication/jsonの独自error.code/messageまで。retry-idempotency README:31/54はSQLiteの業務ledger同時更新と再送で、今回の標準エラー解釈とは別の前提である。

原典本文は上の公式リンク、元教材の実在資料は[前提viewer](related.html?topic=api-readme)から読む予定。本文へのローカル導線と公式リンクのGUI操作確認は別に記録する。画面テストで外部通信を遮断した案内は、公式本文を取得した証拠ではない。
