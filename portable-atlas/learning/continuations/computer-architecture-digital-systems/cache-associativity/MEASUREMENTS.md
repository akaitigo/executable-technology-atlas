# Atlas：保存した模型計算

[root管理の初回計算](observations/attempt-01.json)は11結果・48readを完了しました。これはPythonで計算した論理cache模型で、実CPU cacheの観測ではありません。PID61052、実nice10、正常終了・stderr空・子回収・所有group不在をroot wrapperが保存しています。対象実行1回、自動再試行0、旧教材の実験再実行0です。

[保存検査](observations/attempt-01.verify.json)は手期待と514項目一致し、7個の意味改変をそれぞれ目的のlabelで拒否しました。検査器は模型をimport/再実行せず、保存JSONを読みます。入力拒否の実target比較は今回未実施です。

| trace | direct hit/miss/取得B | 2-way hit/miss/取得B |
| --- | --- | --- |
| conflict | 0/4/16 | 2/2/8 |
| overfull-set | 1/4/16 | 0/5/20 |
| hit-recency | 2/4/16 | 2/4/16 |
| offsets | 3/3/12 | 3/3/12 |
| empty | 0/0/0 | 0/0/0 |

hit-recencyの通常2-wayはvictim block2→4、hit更新省略の故障はblock0→2→4、1hit/5miss/20Bでした。全返却byteが正しくてもLRUの規則は異なります。空traceのhit率はnullです。

入力・手期待・実装は[実行前manifest](records/preexec-inputs.json)で固定しました。rootの実行記録は `../coordination/after-180-runtime/architecture-cache-associativity-20261007T053431010632Z/execution.json`（この教材ディレクトリを基準とした場所）です。これをHTTP内の資料リンクとして扱いません。fresh観測・単独枠・timeout・回収は模型のJSONだけでは証明しないため、最終状態記録でroot実行記録へ結びます。0.080秒という経過時間をcache性能として比較しません。

[実装前手表](HAND_TRACE.md)・[画面確認範囲](GUI_VERIFICATION.md)・[現在状態](status.json)を分けて確認できます。GUIの実施範囲は別記録で確認します。
