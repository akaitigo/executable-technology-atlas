# Atlas：装置の状態を忘れたsnapshot

PC、A、メモリーが戻れば続きも同じでしょうか。小さいタイマーの途中位置と保留状態を含めて保存する場合と、装置だけを既定値へ戻す故障を、4つの命令境界で比較します。

1. [前提](PREREQUISITES.md)でTiny8とSTOREを確認します。
2. [学習画面](index.html)の条件ボタンをクリックし、継続結果が一致するかを予想します。
3. 保存結果を開き、切断点のcounter/pending、次のREAD、最後のmemoryを順に比べます。
4. [契約](CONTRACT.md)と[手計算](HAND-CALCULATION.md)、[実装](model.py)、[原典](SOURCES.md)へ進み、答えを開きます。[Skill](SKILL.md)は問い別に案内します。

## 保存するのは何のためか

snapshotは、その時点から続けるための状態です。counterは周期3のどこまで進んだか、pendingは発火をACKまで保つboolです。READでpendingをAへ取り込み、STOREでメモリーに残します。割込みハンドラーへ自動的に飛ぶ機構はありません。

|切断点|完全復元|装置を省略した比較版で読む点|
|---|---|---|
|初期、tick0|継続と一致する期待|まだ履歴がなく、故障版も一致する|
|発火直前、tick2|同上|counter2を失うと発火時点がずれ、tick4のREADが1→0|
|発火済み、tick3|同上|pending=trueを失うとtick4のREADが1→0。後でpendingが追いついてもmemory差が残る|
|ACK後、tick6|同上|deviceは0,falseなので、この切断点では故障が表に出ない|

prefixは保存地点まで、suffixはその後の続きです。各命令で **tick増加→timer更新・発火→命令→pc進行** の順です。tick6は発火してからACKで消します。画面の全suffix表と選択中の境界を分け、復元直後の状態差と、後のREAD差を混ぜません。

## 正常な形式検査と故障比較

完全restoreはschema/version/機種、必須欄、型と範囲を先に検査します。欠落を黙って補いません。装置を省略する比較版は別schema・別関数で、意図的に0,falseを補います。この故障経路が正常restoreで許可されたという意味ではありません。

本単元は既存の幅やコードキャッシュの原理を増やして数えず、「見えるCPU状態以外も継続に必要」を有限な列で確かめます。実VM、QEMU/HVF、互換性、隔離、物理時間、live migration、任意プログラムの決定性は未実証です。保存形式は独自JSONで、QEMUの形式ではありません。

## 実行と保存画面

計算は2026-10-07 07:04 UTCに1回保存しました。4条件・3経路の99境界/87更新/33READ/26発火を手表へ照合し、25入力拒否と保存値16改変の検出を確認しました。実画面は4条件の全33選択境界、3経路の状態、予想と答え、拒否・復帰、資料7件を確認しました。記録は[GUI-QA](GUI-QA.md)で操作と画像の範囲を分けています。[status.json](status.json)が現在状態、[contract-lock.json](contract-lock.json)は実装前の固定対象です。[保存計算](observations/result.json)、[保存検査](observations/verification.json)、[実行管理の参照](observations/root-run-reference.json)、[実画面の参照](observations/gui-evidence.json)を分けています。

対象計算は既存Python標準ライブラリで `python3 -B observe.py`。低優先度・時間上限・資源条件を確認する外側の実行管理だけが1回起動し、stdoutを保存します。模型内でhost clockをtimerに使いません。runのUTCは計算記録の由来で、guest tickとは別です。

画面は保存結果を表示するだけです。このディレクトリで `python3 -B serve.py --port 0` とするとループバックへ静的配信し、表示されたポートを開けます。制作時のブラウザー確認は共有の1ページを管理する側が行います。保存画面の配信は静的読取りだけです。共有前提へのリンクはこのHTTP範囲外です。

図の上下がpending、数字がcounterである説明を、初回撮影後に1文補いました。数値・配置・操作は不変で、撮影時の版と文面差分を保持します。この追記後の再撮影はしていません。COVERAGEは契約時点の固定資料、現在状態はstatusとGUI-QAで確認します。
