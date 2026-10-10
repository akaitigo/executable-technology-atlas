# 有限検証

事前固定fixtureと手書きCPU/所有/blocked/実効優先度の表を使う。4条件（PIなし/あり×H期限4/2）の全36境界で独立prefix-service oracleがremaining/state/finish/miss/ready/blockedを照合。取得・解放イベントの順を別検査し、仕事量8tickを保存する。Hのblock開始t1、終了t7/t3、blocking6/2を固定照合。実OS時間測定ではない。

不正mode・期限の入力拒否を正常な期限missと分離。CPU順、owner、実効優先度、blocked、blocking、deadlineの誤証拠を検出する。Skillはauthor smoke、独立AgentEvalではない。原票初回実行時刻とQA/seal時刻は別に記録する。

実機IABで4条件×9境界=36表示を読み取った。予想変更で新予想保持・旧比較/答え消去、条件変更で予想も消去、不正tick -1/9/空欄で既存予想対照と現在境界を保持。6画面captureは実取得・ツール内表示済み、ファイル未保存。元教材・独立oracle・producer・関連教材の本文を読んだ。関連リンクは最初HTTP404のHTMLを表示したため、read-only preview mappingとviewer非2xx拒否を修正し再確認。失敗記録はlink-iteration-failure.txt。

自分のタブ19/20と一時サーバー2個は終了。保護ポート53478/PID3901と60285/観測PID80282は維持。60285の依頼時PID64319からの変更はpreview前の外部変更として記録。initial receipt/QAは初回時点、raw timestampは初回実行、seal receiptは後続QAと現在sourceを別時刻で束ねる。全Gate・旧Subjectの実行・commit/pushは行わない。

## 開いた答えの更新

予想だけの変更は新予想を保持し、比較・答え・開いた実務本文を空にして閉じる。条件変更は予想もリセットする。再比較後にだけ実務本文を再び開ける。位置拒否は比較と開いた本文を保持する。初回rawと旧UI/receiptをanswer-historyに保存し、新しい修正receiptで現sourceへ束縛する。
