# hash衝突と容量倍増の論理費用

同じbucketの別keyを保持できるか、拡張でどれだけentryを移すかを実Pythonで確かめる有限教材です。[既存学習経路](../../../subjects/algorithms-data-structures/LEARNING_PATH.md) §6実験2の独立実装であり、既存検索教材やその記録は変更していません。

最初に[有限契約](CONTRACT.md)と[手表](hand-oracle.json)を読みます。次に画面で予想→同じ操作列を固定/倍増へ実行→正常/意図異常→実装・list oracle・原票→答えの順で進めます。条件や予想を変えると以前の結果を消します。

## 再現

Python 3.9以上、標準ライブラリのみ。install不要。このディレクトリで `python3 -B serve.py` を起動し、表示された127.0.0.1のURLを開きます。別terminalで `python3 -B verify.py` または `python3 -B route.py` を実行します。serverはCtrl-Cで終了します。Macのsandboxがloopbackを拒否した時はその失敗を残し、通常のhost許可reviewを経ます。sandbox無効化を手順にしません。

`verify.py --record attempt-01` は初回記録用です。既存原票がある時は再記録を拒否します。通常verifyは再実行結果・source hash・封印済み観測を読み取り、ファイルを書きません。UI確認後の `--seal-record` は初回receiptを残して現在の束縛を保存する作成者向け手順です。

## 観測の読み方

正常collision列は固定が比較14/移動0、倍増が比較9/移動3。distributedは12/0対4/8。persistentは両方比較27で、倍増でも0,8,..40が同bucketへ残ります。thresholdはn==mと更新で拡張しません。negativeは-1%2=1、空find/deleteは比較0です。

意図異常delete-whole-bucketは一致keyを見つけたbucket全体を消します。拡張で削除対象が単独になれば正常と一致します。異常側手予想のcollision/doublingを初回誤りから訂正した記録を[残しています](observations/core-hand-correction.json)。実装に合わせて失敗を消していません。

比較は訪問chain keyごとの一致判定、移動はrehashで新bucketへ配置したentryです。hash計算・bucket走査・allocation・list shift・oracle・UI費用を含みません。削除でデータを失って比較が減ることを性能向上とは呼びません。期待O(1)・実時間・分野全体の完了は主張しません。[COVERAGE](COVERAGE.md)に未対応を残しています。

## 原典と証拠

[MIT Lecture 8/9本文の確認](sources.json)、[chaining実装](chaining.py)、[hashを使わないlist oracle](list_oracle.py)、[検査器](oracle.py)、[CLI原票](observations/attempt-01.json)、[検証範囲](VERIFICATION.md)。第三者本文・図・コードを転載していません。UIの図は実応答traceの説明用描画です。実画面captureはtool表示で確認し、保存できない場合はsaved=falseと記録します。
