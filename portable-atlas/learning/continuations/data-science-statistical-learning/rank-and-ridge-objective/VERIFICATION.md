# 保存原票と独立照合

hand-oracle.jsonをproducer前に保存。rawには入力・source hash・UTC・command・exit・7条件・196目的差照合・17入力拒否・6改変拒否を記録する。oracleは消去法を共有せず、閉形式、literal rank/Gram/係数/目的と各正常方程式、目的差の平方展開を照合。Fractionの完全一致でありfloat安定性の検査ではない。

通常verify/routeは再計算・raw・source/artifact receipt照合のみ。明示recordは未使用attempt、sealは初回receiptを残して現sourceを束縛する。IABで予想だけのclear、条件reset、成功後の拒否/失敗、点表示破棄、範囲外位置保持、リンクを実操作する。実captureツール表示とファイル保存を区別し再構成しない。自作loopback server/tabのみ終了し保護listenerを変更しない。
