# テスト順とfixture隔離

結果の分母を解釈した次に、再現性とtestの独立性を確認する教材です。品質要求 → 測定の分母と未知 → テスト選択 → 結果解釈 → 再現性と独立性の順で、画面のRequirements/QE/直前mutation/既存Software Quality入口へread-only接続します。旧教材・原票は変更しません。

1操作で、指定条件の同じ2テストを新しいPython processで2回実行します。子process内の整数discountだけが共有state。quote=10-discountで、overrideはdiscountを2へ変えて8をassert、defaultは初期0を前提に10をassertします。

| 状態の扱い | test順 | 2 attemptのexit | 原因 |
|---|---|---|---|
| shared | override→default | 1,1 | discount2が残りdefaultで8≠10 |
| shared | default→override | 0,0 | defaultが先に0を読む |
| fixture | override→default | 0,0 | 各setUp/tearDownで0へ戻す |
| fixture | default→override | 0,0 | 同じassertionを維持して隔離 |

実装前のhand-oracleはsetup/body/teardown前後、期待値/実値/outcome、最終stateとexitを固定。worker.pyの同じtest methodを両版で使い、assertEqualを弱めたりskipしません。unittestが本当にtest集合を実行し、故障版のAssertionErrorも生stderrへ残します。ATTEMPTS_RECORDEDは証拠がそろった状態で、全test成功という意味ではありません。

`python3 -B verify.py`と`python3 -B route.py`で4条件×2 child attempt・13拒否・7mutantを検証します。毎回実processが走り、PID/UTC/elapsed表示は変わります。保存原票のsemantic値と独立手表を照合し、保存原票を更新しません。通常再現でrecord/sealを再実行しません。`python3 -B serve.py`の127.0.0.1動的portを開き、予想→順序/隔離→実行→state図→全exit/stdout/stderr→source→答えを読む。自身のserverだけCtrl-Cで終了します。追加package不要。

観測はcore-first-attempt.json（最初の核心経路）、attempt-01.json（制作時のCLI全8 attempt）、browser-cases.json/UI QAに分けます。verifyの新しい再検証は全8 attemptをoracleへ照合しますが、読み取り専用なので保存原票へ追記しません。都合のよい再実行だけを選んだ成功率は作りません。ブラウザ圧縮投影は実DOM観測後の転記で全文raw downloadではありません。capture未保存ならpath/hashを作りません。source viewerは長文を32768文字の明示抜粋と完全ファイルへのリンクで示します。

[Python 3.9 unittest](https://docs.python.org/3.9/library/unittest.html)のfixtureと明示TestSuite順序を参照。取得文書は3.9.25、実Mac runtimeは3.9.6です。[pytest Flaky tests](https://docs.pytest.org/en/stable/explanation/flaky.html)のSystem stateは概念参照だけ。stableはrolling文書で取得本文に数値版がなく、pytestを導入・実行していません。

5秒の子process終了上限は安全な実行境界で、実timeoutを発生させた教材ではありません。共有設定は子processに閉じ、OS環境・ユーザー設定を変えません。固定順序で決定的に再現したtest間state漏れの例であり、OSスケジューラ、実並列race、全flaky原因、実CI製品品質や全科目/Coreは未評価。
