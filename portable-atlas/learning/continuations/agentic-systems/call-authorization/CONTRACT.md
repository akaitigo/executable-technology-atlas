# Atlas — 型が正しい呼出しと、承認された呼出し

この契約は実装・計算より前に固定する。合成した計画、観測、承認だけを使う有限模型であり、LLM、API、MCP、実ユーザーの承認、OS権限、外部への送信を実行しない。

## 前提と新しい問い

JSON、整数と文字列の違い、状態遷移、型付き参照は前提。既存教材は `r.value` を整数として取り出すところまでを扱う。本単元は、その整数で組み立てた具体的な呼出しが、外から固定した承認と一致するかを実行直前に判定する。

読む順は、予想 → 許可された処理名と型 → 観測の参照 → 承認照合 → 実行／拒否の対照 → 原典・実装 → 答え → 実務判断と限界。

## 固定した入力と段階

- 計画は `read-r`、`add-a` の2段階。read は合成fixtureの深いコピーだけを返す。ファイルやネットワークを読む処理ではない。この固定readは模型の実行規約で許可済みとし、今回の呼出し別承認の対象はaddである。
- addは `a = r.value`, `b = 3` の純粋な和。値は `type(v) is int`、各−100〜100。bool・文字列から変換しない。
- 最初に計画全体の処理名と参照構造を検査する。未知tool等の不正入力ではreadも実行しない。read後に観測のrequest IDとfield/型を検査し、失敗ならread 1回、add 0回。
- 観測は今回の `request-1` のみ有効。別requestに由来する値は、同じ整数4でも拒否する。前回の値・答え・承認を流用しない。
- 承認は `external-fixed` の入力からのみ読む。actor、計画のSHA-256、call ID、tool、具体的な引数a/b、期限、使用済み状態を含む。承認者の認証や署名はない。hashは固定byteの同一性を比較する値であり、同意・真正性・権限を生まない。
- JSONのhash規約はUTF-8、ASCIIの識別子、keyを整列、空白なし、整数表記。計画hashは計画全体、call hashは `{actor,plan_sha256,call_id,tool,args}` を対象とする。固定byte列も保存する。
- 論理時刻は整数0〜20、期限は10。`now < expires_at` の場合だけ有効。時刻10ちょうどは期限切れであり、実時計の測定ではない。
- 承認照合の順は、存在 → actor → plan → call ID → tool → args → 期限 → 未使用。最初の不一致で停止する。正常では同じ逐次処理内で使用済みにしてからaddを1回呼ぶ。並行処理・クラッシュ後の再利用・永続的な原子性を保証しない。

## 11条件の手計算

| 条件 | 承認照合／停止理由 | read / add | 最終値 | 承認の使用前→後 |
|---|---|---:|---:|---|
| normal | 外部承認と全項目一致、時刻9 | 1 / 1 | 7 | false→true |
| args-changed | 観測100は型に合うが、承認はa=4：ARGS_MISMATCH | 1 / 0 | null | false→false |
| plan-changed | 同じ処理でも計画versionが別：PLAN_MISMATCH | 1 / 0 | null | false→false |
| call-changed | 実call IDはadd-aのまま、承認側だけadd-other：CALL_MISMATCH | 1 / 0 | null | false→false |
| expiry-at | 時刻10、期限10：EXPIRED | 1 / 0 | null | false→false |
| missing-grant | 観測に承認らしいデータがあっても外部承認なし：NO_APPROVAL | 1 / 0 | null | null→null |
| bad-data-approval | 意図的誤り。missing-grantと同じ入力から、観測内の承認を採用 | 1 / 1 | 103 | false→true（偽の出所） |
| binding-type | 観測は文字列"4"：TYPED_INT。承認照合に未到達 | 1 / 0 | null | false→false |
| stale-observation | 値4でもrequestが旧版：STALE_OBSERVATION。承認照合に未到達 | 1 / 0 | null | false→false |
| consumed-grant | 既に使用済み：CONSUMED | 1 / 0 | null | true→true |
| actor-changed | 実行主体bob、承認alice：ACTOR_MISMATCH | 1 / 0 | null | false→false |

正常は1件、期待した拒否は9件、意図した誤実装は1件。bad-data-approvalはBAD_COMPLETED、authority_breach=trueとし、103が計算できても承認成功に数えない。missing-grantとの違いは方針だけで、入力は同一にする。readは両方で実行済みなので、拒否を「全呼出し0」と説明しない。未到達の具体引数・call hashはnullとする。authorizedは最終的に許可できたかを表すため、照合未到達でもfalse。authorization_reached=falseとし、個々の照合項目はnullで未到達を示す。

## 受入と実行上限

実装前手表とは別の検査で、入力の固定byte・全11結果・停止位置・呼出し順・使用前後・故障対照を確認する。入力拒否と保存結果の改変拒否を分離。実計算は資源確認と独立レビュー後、同一子のnice実値10、Python子1件、観測5秒・別回収猶予2秒、自動再試行なし。未回収なら次の起動を禁止する。

画面は保存結果を読む。予想・条件・記録の変更、reset、欠落／改変の拒否で古い結果・答え・開いた詳細を消し、正常記録への復帰を確認する。実DOM・実画像は別の確認であり、静的検査では代用しない。Skillは具体引数の差替え、期限境界、tool-dataの承認への昇格を案内する。

## 残る限界

実認証・承認UI・署名・秘密鍵・LLM防御・OS capability・外部副作用・並行原子性・耐久性・実時計・一般的な攻撃耐性は未検証。モデル内の外部承認も固定fixtureを信頼する仮定である。一般的な認可や既存の型付き参照を新規達成として数えない。
