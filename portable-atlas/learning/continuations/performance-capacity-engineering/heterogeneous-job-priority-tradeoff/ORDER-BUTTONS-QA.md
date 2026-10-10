# Atlas：クリックで順序を選ぶ操作の確認

既存の選択メニューを残し、「前の順序」「次の順序」を追加しました。どちらもメニューと同じ条件更新処理につながり、予想・答え・時刻をリセットします。最初のABCでは前へ、最後のCBAでは次へを無効にします。

根拠となった操作記録は [メニュー確認](../browser-qa/menu-usability-2026-10-06T074257187Z/report.json) です。OSの選択メニューへの自動キー入力で値が変わらなかったため、通常のクリックで選べる経路を補いました。メニュー自体を手操作で選び切れることの確認とは別です。

2026年10月6日08:11 UTCの [操作記録](observations/order-buttons-browser-2026-10-06T081139594Z/report.json) は17項目、39回の実クリック、6順序の表示で成功しました。プログラムによる選択値変更は0回です。前後ボタンで6順序へ移り、両端の無効化、予想・答え・時刻の消去、既存リセット、幅1280px・390pxの横溢れなしを確認しました。実際の画面から読み取った各仕事の完了時刻も手計算に一致しています。

|画像|幅・場面|
|---|---|
|[最初の順序](observations/order-buttons-browser-2026-10-06T081139594Z/desktop-first-disabled.png)|1280px、ABCで「前の順序」が無効|
|[最後の順序](observations/order-buttons-browser-2026-10-06T081139594Z/desktop-last-disabled.png)|1280px、CBAで「次の順序」が無効|
|[全ページ](observations/order-buttons-browser-2026-10-06T081139594Z/mobile-buttons-full.png)|390px、BCA・時刻2・答え表示|
|[操作部分](observations/order-buttons-browser-2026-10-06T081139594Z/mobile-buttons-controls.png)|390px、BCAの前後ボタンと予想|

作者が4枚を目視し、ボタン・予想・日本語の折返しに表示を妨げる問題は見つかりませんでした。[目視記録](observations/order-buttons-visual-review.json) と [終了確認](observations/order-buttons-browser-2026-10-06T081139594Z/cleanup-check.json) を保存しています。専用ブラウザーを終了し、一時プロファイルを削除しました。ローカルファイルを直接開いており、サーバーは起動していません。

以前の受入は [変更前の受入記録](../acceptance/capacity-priority/acceptance-before-order-buttons.json) に保持しています。今回の変更前ファイルは [保存済みの前版](observations/before-order-buttons/manifest.json)、現在の確認対象は [今回の引渡し記録](observations/order-buttons-handoff.json)、別担当の判断は [独立受入記録](../acceptance/capacity-priority/acceptance.json) から追えます。初回の計算結果・画像・検査記録は置き換えていません。撮影後の変更は説明文書とその対応情報だけです。

計算式と仕事の入力は変えていません。今回はボタンの操作改善に絞り、以前の全48状態・32画面時点の検査を再実行していません。OSの選択メニューそのものの手操作、実サーバー性能、別ブラウザー・実端末は未確認です。これは既存教材の改善であり、教材数を増やす変更ではありません。Atlas全体台帳は変更していません。
