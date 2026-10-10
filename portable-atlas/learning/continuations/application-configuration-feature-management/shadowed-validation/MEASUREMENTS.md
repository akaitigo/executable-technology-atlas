# 保存した模型計算

[初回結果](observations/attempt-01.json)は12比較をcomplete/exit0で保存しました。成功4、契約上の設定拒否8、全87eventです。設定拒否は実行失敗とは別です。[保存値検査](observations/attempt-01.verify.json)は1191照合と7つの意味改変を目的labelで拒否しました。模型のimport/再実行はしていません。独立手表へも12結果/全87時点が一致しています。

模型実行当時のroot資源gateはfree39%で当時の基準40%未満となり、target未開始のholdです。その後の新しいfresh gateはfree49%、load3.13/idle88.72で成立し、初回targetだけを実行しました。このfree割合は物理的な未使用RAMやOS安全境界を意味しません。対象の自動retry0です。PID390/実nice10/約0.077秒/exit0、子回収・groupAbsent、終了signal0をroot実行記録から読みました。

rootが外側wall5秒を管理し、RLIMIT_CPUは継承値として保存しています。別のCPU時間上限や速度の優劣は主張しません。実行記録の場所（教材directory基準）は `../coordination/after-186-runtime/config-shadowed-validation-20261007T075542956111Z/execution.json`。単体HTTP内のリンク成功とは扱いません。

画面接続前のnull bundleもその時点のbyteで保存しました。これはroot実行後の保存であり、target前のsnapshotとは呼びません。JSON型を保ち、falseと0を別に照合します。未知fieldのrawは結果/eventへ転載せず、fixtureの保存とは別の境界です。型parseとJSON構文解析、部分候補と公開設定を分けて読んでください。

上位指定を外すと下位不正が現れ得るという説明は契約からの推論で、remove/reloadを実測した主張ではありません。未知field以外の任意schema拒否、実環境/秘密保護全般、provider呼出しは未実行です。[現在状態](status.json)と[GUI範囲](GUI_VERIFICATION.md)へ。

GUI実施時にはrootのメモリー判定が、旧40%/概算2GiBからOS pressureとswap変化を使う規約へ更新されています。旧模型・保留記録は書き換えず、旧gateのSHAを完全一致のbefore保存ソースへ解決しました。[対応記録](records/gate-source-resolution.json)で当時の模型と今回GUIの版を分けます。将来の安全や全用途に共通する閾値を実証したものではありません。
