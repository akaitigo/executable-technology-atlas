# 配布用の観測データ

このreaderは、過去の固定観測から計算結果・固定期待値を保持し、端末pathや実行管理情報を除いた配布用コピーを読みます。schemaVersion 2 と配布用SHAを検査し、破損・別契約を拒否します。原本の受入票を検査した意味にはしません。

元 data.js・埋込みtext・run text・expected text のSHAは migration-provenance.json に保持しています。非environmentの全recordと固定期待値は原本と一致します。元原票そのものは私的保全manifestの対象です。

復元には、この教材directory内の index.html、lesson.js、data.js、CSS、実装・入力・固定期待値をまとめて配置します。root READMEのNode readerで開けます。compilerや外部APIは保存再生に不要です。data.jsが破損した場合は配送manifestと一致する同名fileを復元してください。現在の原票に旧SHAを付けたり、未実施の再計算を実測と扱ったりしません。

局所JS検査と固定値照合は実施し、ブラウザの描画・実ポインター操作は未検証です。
