# Atlas：保存した有限計算

[実行ログ](observations/attempt-20261006T195709350667Z/run.json) と [照合結果](observations/attempt-20261006T195709350667Z/verification.json) は、固定6列の一回の計算です。Python子1件、再試行0、実nice10、約0.172秒、exit0、所有子回収済み。実threadや無限時間を動かしたものではありません。

|固定列|公平性なし|WF両process|SF入室1のみ|WF両＋SF入室1|P1の飢餓|
|---|---|---|---|---|---|
|Aで停滞|true|false|false|false|true|
|Bで停滞|true|false|false|false|true|
|P0保持中に停滞|true|false|true|false|true|
|P0が取り続ける|true|true|false|false|true|
|両者が進む対照|true|true|true|true|false|
|以前の入室後に再要求|true|true|false|false|true|

Atlas の各行は「その仕様でこの列を許すか」です。P1の飢餓とは別の判定です。両者がtrueなら、その仕様で許される飢餓反例になります。6列から全graphの性質を証明したとは扱いません。

前提graphの8状態/14非停滞辺と追加停滞8辺、prefix計11辺とcycle計15辺、要求の順序、入力14件のhash、完全stdout/stderrを保存しました。作者側は186照合、保存コピーへの8改変を拒否。別担当の確認と実画面の範囲は [状態記録](status.json) から辿れます。

実行前にはsandbox内のtop/ps読取不明、追加browser検出という二つの停止があり、対象はいずれも起動0でした。親が保存観測に基づく57厳密identityの今回限りの条件を明示した後、fresh load3.994・idle84.74%・メモリ空き59%で成立しました。以前の停止を成功へ変更せず [履歴](records/resource-hold.json) と [運用条件](RUN_CONDITIONS.md) に分けています。他の既存processの設定や終了は行っていません。
