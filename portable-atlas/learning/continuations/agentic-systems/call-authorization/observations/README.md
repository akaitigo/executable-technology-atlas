# Atlas — 保存した記録への入口

保存計算は [calculation-20261006T205623999075Z/report.json](calculation-20261006T205623999075Z/report.json) と [結果](calculation-20261006T205623999075Z/result.json)。正常1・期待拒否9・故障比較1、入力拒否13、実nice10、0.214秒、exit0、子の回収完了、自動再試行0です。

通常の読取検査：`python3 -B verify.py observations/calculation-20261006T205623999075Z`。計算を再実行せず、全履歴と12種類の保存値改変拒否を確認しました。[検査結果](saved-calculation-check.json)、[画面データとの対応](reader-connection.json)へ進めます。

- [実装前の手期待](../hand-oracle.json) と [固定byte](../fixed-bytes.json)
- [初回の資源確認](resources-20261006T204943602398Z.json)：余力はあったが、未分類の既存ブラウザーがあり停止。模型は未起動。
- [実行前の対応](preexecution-handoff.json)、[所有資源の注入検査](ownership-check.json)、[余力の境界](cli-policy-v2-check.json)、[識別の境界](identity-check.json)

実計算、入力の期待拒否、故障比較、画面の操作を別の記録として読みます。保存した過去の停止や修正前のsourceは置換しません。
