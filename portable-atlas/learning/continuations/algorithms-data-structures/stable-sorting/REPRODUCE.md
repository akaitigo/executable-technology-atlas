# Atlas｜計算と画面の確認を分ける

既存MacのPython標準ライブラリだけを使用しました。install、SDK更新、DockerやOS設定変更は不要です。

今回の実行は2026-10-06 17:57:21 UTC、実nice10、6入力×3方式・8拒否例、計算0.0225秒です。[実行ログ](verification/execution.json)でrun/verifyの逐次終了を確認できます。既存runは再実行して上書きしません。

1. [契約](CONTRACT.md)、[固定入力](fixture.json)、[実装前の期待](expected.json)、[拒否例](rejection-cases.json)を読む。
2. 実行前に全体CPU/load・メモリと他の重い処理を確認する。確認できない場合は実行しない。execute_once.pyは実際の優先度を10へ下げて読戻し、失敗したら計算を開始しない。run.py、verify.pyを1個ずつ各15秒以内で実行し、既存runを上書きしない。
3. 保存した計算だけを確認する場合は、`python3 -B verify.py`。新たな整列実行とは区別する。
4. 2026-10-06 18:57 UTCに既存の公式Playwright/Chromium headless・sandbox有効の共有1ページで画面を確認した。18選択・57段階、変更/reset、取得失敗からの回復と古い応答の無視、1280/390pxの3画像を保存。担当の経路設定は解除しviewportを戻した。共有ページとserverの終了は所有する実行担当が管理する。

画面の起動は `python3 -B serve.py --port 0` の専用loopbackを用い、表示されたATLAS_PORTへ既存の確認ページで移動する。固定allowlist以外は配信しない。既存サービスを停止せず、衝突時は空きportを選ぶ。原典や前提のviewerも、指定した既存2文書だけを読取表示し、元文書は変更しない。

Atlasの関連2資料はhref取得後に同じページへ移動し、固定本文へ照合しました。リンクの実クリックは未確認です。計算の再実行は不要で、状態文だけの追補確認は初回の全条件確認と分けて保存します。
