# 非秘密の入力と再生成の範囲

保存readerのために非公開の画像や生DBを取得する必要はありません。配送manifestに含まれる選別済みの保存値と固定入力を使います。教材の入力・モデル候補は [再生成入力索引](../app/lib/reproduction-inputs.json) で各READMEと対応付けています。索引は収録ファイルの存在とSHAの確認であり、191教材すべてのproducer実行合格ではありません。

## 小さなSQLite seed

`seeds/wal-snapshot-values.json` はWAL教材で使う架空の整数8条件です。個人DB・認証情報・時刻・端末情報を含めず、表と値だけを新しいDBへ生成できます。Python 3.9以上の標準sqlite3を使い、installやネットワークは不要です。

配送treeの外側で、まだ存在しないdirectoryを指定します。親directoryは先に存在する必要があります。

```sh
python3 scripts/rebuild-seed-databases.py --output-dir ../atlas-seed-output
npm run test:seeds
```

8個のSQLiteと `seed-result.json` が生成されます。既存directory、配送tree内、重複ID、不正なpath、非整数を拒否します。SQLite版によりDBのbytesが異なる可能性があるため、再生成結果はschema・行の値・integrityを照合します。同梱済みの保存DBを上書きしません。

このseedで再現するのは `evidence(id,value)` の合成値です。WAL競合の過去の発生順、runtimeエラー、操作画面、実測時刻は再生成しません。新しいWAL実験は教材のnative手順と環境条件を確認する別工程です。

## Gitに含めないもの

過去のcapture画像・実測全文原票・個人情報のある検証記録は、同じ結果を生成するコードがあっても過去の証拠そのものには戻せません。必要性が未判定のものを不要扱いせず、非公開archiveと元SHAを保持しています。画像・原票が必要なら、本人が決めた非公開保全先から復元します。未検査画像を公開用seedとして扱いません。

一般cache、依存package、SDK、認証store、旧端末の実行管理情報は、このreaderの移行セットには含めません。新しい実験にSDKが必要なら各教材で前提を確認し、新PCで本人が認証します。元のファイルは削除していません。

正式142・候補追加6・その他未統合43の区分、過去原本SHAと配布用SHAの区別を保ちます。seed生成やGit移行で受入・中央統合を増やしません。
