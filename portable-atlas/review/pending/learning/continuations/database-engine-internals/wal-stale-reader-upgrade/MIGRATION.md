# WAL教材の保存再生と復元

index.html は固定13条件（過去の観測8・入力拒否5）をSHAと固定期待値で照合して表示します。入力は選択式で、保存結果のない入力は生成しません。SQLite producer、専用API、外部サービスは保存再生に不要です。

observation-data.js は元ファイルと同一byteです。含まれる8個のbase64 SQLite DBを復号し、保存SHA、8192 bytes、2ページ、freelist 0、evidence表だけのschema、整数1行の期待値、quick_checkを読み取り専用で確認しました。DB header 100 bytesとWAL header 32 bytesも形式を確認しました。画像や一般の未知DBを許可した検査ではありません。

saved-db/ に8個の同一DBを保存しています。由来・SHAは migration-provenance.json で確認できます。データはこの教材で生成した架空値で、ユーザーDBではありません。保存SQLiteを開く場合はcopyを使い、元の配送SHAを保ってください。

復元は、この教材directory全体とroot readerを配送manifestどおりに配置します。Node.js 22.13以上でroot READMEのreaderを起動し、未統合一覧から開きます。画像・compiler・別repo・ネットワーク接続は13条件の再生に不要です。

元の実SQL UIを native.html / native-app.js、producerを evaluator.py / native.py、専用serverと固定検査を既存ファイルに残しました。実SQLを新環境で行うには、そのPython・SQLite公開C API・loaderの対応を確認し、元READMEのlocalhost手順を個別に実施します。今回、そのproducer・専用API・browserは実行していません。

元の実行原票は observations/ 配下と私的保全manifestで位置とSHAを確認できます。全文原票を復元する場合は、その保全元から同じSHAを持つ原本を取得し、現在のデータを過去の原票に見せかけて置換しません。
