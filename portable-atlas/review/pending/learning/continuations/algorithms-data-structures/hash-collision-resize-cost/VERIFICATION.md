# 検証範囲

実Python標準ライブラリ、Mac既存環境で正常/意図異常の24条件を実行します。単純list oracleはchaining/hashをimportせず、各stepのfound/value/action/全entryを別に算出。検査器は訪問key・比較数、bucket余り、n・容量、移動先、全stepの意味と手表の正常費用・異常不一致stepを照合します。12設定拒否、9操作拒否、8結果変異を検査します。拒否で状態を変更しません。

実ブラウザUIは同じ列を選択方針と対の方針へ実行します。各有限条件の両費用・不一致step・最終entryのコンパクト投影をCLI原票と照合し、表示traceは実応答から生成します。ブラウザ投影は完全な原票downloadではなく、検査した範囲を観測JSONに明記します。条件/予想変更、reset、古い保留応答、通信失敗、source読み戻しを別に検査します。

原票attempt-01は初回生成後に上書きしません。receiptはsourceと原票SHAを束縛し、UI後のsealで初回receiptを保存します。最終read-only-proofはverify/route/Skill検査の前後SHA・mtime不変を記録し、最後に生成します。Core atlas audit/npm gate、コミット、push、公開は未実行です。画面図は論理数の説明であり実時間の測定ではありません。
