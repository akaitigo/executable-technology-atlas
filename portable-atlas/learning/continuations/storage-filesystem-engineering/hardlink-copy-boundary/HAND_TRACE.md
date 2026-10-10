# Atlas：hardlink と copy の実行前の手計算

入力は改行を含む6byteだけです。`ALPHA\n`をoriginalへ新規作成し、同じ対象を指すaliasをhardlinkで追加します。copyには読み取った6byteを、新しい通常ファイルへ書きます。

| 時点 | original | alias | copy |
|---|---|---|---|
| 新規作成 | A / nlink 1 / ALPHA | なし | なし |
| hardlinkとcopy作成 | A / 2 / ALPHA | A / 2 / ALPHA | B / 1 / ALPHA |
| 存在するaliasへ再link | A / 2 / ALPHA | A / 2 / ALPHA | B / 1 / ALPHA |
| alias経由の同じ長さの上書き | A / 2 / BRAVO | A / 2 / BRAVO | B / 1 / ALPHA |
| copy経由の同じ長さの上書き | A / 2 / BRAVO | A / 2 / BRAVO | B / 1 / COPY! |
| originalという名前をunlink | なし | A / 1 / BRAVO | B / 1 / COPY! |

各文字列は末尾に改行があります。`nlink`は同じファイル実体を指す名前の数です。`inode`はファイル実体を識別する番号で、デバイスの番号`dev`と組にして比べます。A/Bは今回1回の実行内の`(st_dev, st_ino)`へ後から対応させる説明用記号で、具体的なinode番号を予想していません。AとBは別の組、hardlinkの二つの名前は同じ組を予想します。

既にあるaliasを宛先にしたlinkは`EEXIST`、Pythonでは`FileExistsError`を予想します。これは意図した失敗で、正常なlink作成と別に記録します。失敗前後の内容・identity・nlinkは不変と予想します。

copy側の上書きは、この有限操作でoriginal/aliasのbytesへ伝わらないことを比較します。物理blockの非共有やすべてのmetadataの独立を予想する表ではありません。unlink後も開いたFDから読む試験は既存OS教材にあり、今回は行いません。元の名前を消した後、残っている名前を新しく開いて読みます。

この表と[expected.json](expected.json)を実行前に保存します。まだ結果ではありません。実行後は数値をこの表へ都合よく合わせず、測定結果と照合します。
