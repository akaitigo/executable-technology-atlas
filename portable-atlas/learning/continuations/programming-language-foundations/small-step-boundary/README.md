# Atlas：一歩進んだのか、ログが一行増えたのか

閉じた小さな構文木を規則で一歩ずつ書換え、同じ入力を旧環境評価器で計算した結果と比べる教材です。値、規則が適用できない行き詰まり、観測予算の終了を分けます。現在の実行・実画面・独立確認は [status.json](status.json) に記録します。5条件の初回計算を保存し、固定した期待へ照合しました。[測定結果](MEASUREMENTS.md)から実行ログへ戻れます。既存の同じページで実画面30項目・全13主要状態を確認し、初回10枚と可読性追補1枚を保存しました。[画面確認](GUI_VERIFICATION.md)と独立受入の現状は状態記録で別に示します。

[前提](PREREQUISITES.md) → [画面](index.html)で条件と予想 → 項の前後・規則と旧ログを比較 → [原典と実装の対応](reference.html) → 答え → [範囲と次の問い](COVERAGE.md)の順に読みます。[限定Skill](SKILL.md)からも同じ道筋を辿れます。自由記述の予想は自動採点しません。

5条件は、値0・加算を3歩で完了・同じ加算を2歩で停止・関数適用・整数の呼出しです。[手表](HAND_TRACE.md)と[期待値](expected.json)を実装より先に固定しました。小ステップの[実装](small_step.py)は期待値を読みません。[旧評価器](inputs/prerequisite-interpreter.py)のイベント列は、関数の出入り等を記録した別の観測です。その1行を規則1歩とは数えません。

## 利用方法

標準の静的HTTP配信でこのディレクトリを公開し、`index.html` を開きます。既存の配信がある場合はそれを使います。ローカルで新しく配信する場合の例は `python3 -m http.server 8765 --bind 127.0.0.1 --directory <この教材の絶対path>` です。画面は保存したJSONを読むだけで、計算器を起動しません。直接file URLでの利用は検証範囲に含めません。Markdown/Pythonは配信MIMEにより本文表示またはダウンロードになり、取得bytesと画面本文を区別します。

対象の再現は[実行条件](RUN_CONDITIONS.md)に従います。現在の所有参照と今回の実行判断を準備し、`python3 -B resources.py --root-slot '<今回の調整記録>' --decision <今回の判断.json> --execute-slot --gui-idle --other-targets-zero` で新しい記録を保存します。成立しない場合は止めます。成立しage60秒以内なら `python3 -B run.py --execute --resource-record records/resources-<今回>.json`。出力先は新規作成され、旧記録は上書きしません。保存結果は `python3 -B verify.py observations/<今回>/run.json --mutations`、画面への接続は `python3 -B build_bundle.py --run observations/<今回>/run.json` です。検査は評価器を再実行しません。読むだけなら再計算は不要です。

## 何を分けるか

- 最初から値なら予算0でも `value`。ちょうど予算を使った完成値も `value` です。
- 規則があるのに予算がない場合は `budget_exhausted`。未適用の次規則は実行した歩数へ足しません。
- 値でもなく規則もない有効ASTは `stuck`。整数を呼ぶ例では引数を先に計算しません。
- 入力の形式違反、資料の取得失敗、対象processの失敗は、上の3分類とは別です。

実装の入力上限はAST64節点・深さ16・入力整数−1000〜1000・予算0〜16です。boolを整数や予算に混ぜません。Let、自由変数を持つ入力、storeや副作用は対象外です。関数内の束縛変数は使えます。これは入力の制限で、一般の型安全性・停止性・評価器の等価性の証明ではありません。旧capture/置換やVM命令の受入を作り直さず、今回実行しないCallFn規則や最終Fn値を検証済みにしません。
