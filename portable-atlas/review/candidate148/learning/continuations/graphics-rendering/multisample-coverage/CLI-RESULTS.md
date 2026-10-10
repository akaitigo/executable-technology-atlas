# Atlas — 保存計算と照合

2026年10月7日04:44 UTCに、Python標準ライブラリの有理数模型を1回だけ実行しました。実GPU・画像品質・色管理を測った結果ではありません。外部要求、GPU API、追加サービスは使っていません。

[実行記録](observations/calculation-20261007T044450218647Z/report.json)は実nice10、exit0、約0.277秒、子の回収済みを記録しています。[直前資源](observations/resources-20261007T044449232650Z.json)からの経過は約0.986秒でした。余力の観測はその開始条件であり、その後のMac全体の負荷を保証しません。メモリーの利用可能量はfree・inactive・speculativeからの推定値です。

[保存結果](observations/calculation-20261007T044450218647Z/result.json)は5条件×2配置、40 pixel結果、100個の最終sampleを含みます。160回の所属判定のうち94回が深度比較へ進み、87回で値を更新し、7回を深度で拒否しました。非所属66回は比較未到達で、採否はnullです。入力不正21件は描画前に拒否し、処理回数0を保持しています。

[読取検査](observations/calculation-20261007T044450218647Z/verification.json)は実装前の固定maskからの別展開と保存値を照合し、18種類の改変を検出しました。模型のimportや再計算はしていません。先に別担当が固定したliteral期待の確認と、作者側の保存検査は分けて扱い、最終受入は別の記録へ委ねます。

```sh
python3 -B verify.py observations/calculation-20261007T044450218647Z
```

このコマンドは保存済みJSON・stdout/stderr・固定資料・実行時sourceのhashを読みます。新しく描画模型を実行するコマンドではありません。現版sourceを変更する場合は実行時版を保存して対応を明記する必要があります。

画面へ接続した記録は[接続情報](observations/reader-connection.json)、状態の有限確認は[210件の検査](observations/reader-state-check.json)です。EXPECTEDは保存データと由来の改変検出用コピーで、独立した数学的根拠ではありません。元の未接続版は[変更前](history/before-reader-connection/reader-data.js)へ保存しています。保存された実DOM・操作・画像の確認範囲は[画面確認の記録](GUI-QA.md)へ続きます。
