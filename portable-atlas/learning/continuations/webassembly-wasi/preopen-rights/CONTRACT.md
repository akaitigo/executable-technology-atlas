# Atlas：事前に渡したディレクトリと、開くための権限

Node.js 25.2.1、uvwasi 0.0.23、WASI preview1に固定した4条件です。目的は「FDがない」「必要な権限がない」「許可された場所で名前がない」「読めた」を区別することです。Nodeは安全なファイルシステム隔離を保証しません。外部パス、第三者データ、シンボリックリンクによる境界越えは試しません。

## 実装前の期待

|条件|事前FD照会|権限変更|ファイルを開く|読み出し|
|---|---|---|---|---|
|ディレクトリなし|BADF 8|未到達|未到達|未到達|
|ディレクトリあり|成功、名前 /lesson|なし|成功|Atlasと改行の6バイト、その後EOF|
|開く権限を減らす|成功|baseからPATH_OPEN 8192だけ除く|NOTCAPABLE 76|未到達|
|許可内の名前なし|成功|なし|NOENT 44|未到達|

[手書き期待表](hand-oracle.json)を実装より先に固定します。FD3はこのNode環境で最初の事前ディレクトリとして確認し、別環境へ一般化しません。通常のopenが返すFD番号は固定せず、成功時の返却値をread/closeへ渡します。fdstatで前後のbaseとinheritingを保存し、権限減少条件はbaseのPATH_OPENだけを除き、inheritingを保持します。開く際に新FDへFD_READ 2を要求します。

失敗したpath_openの出力領域、失敗したreadの長さは有効な値として読みません。未到達はnull、読めた空列やEOFと区別します。正常読み出しは最大8回・各8バイトで合計6バイトとEOFを確認し、途中読みの回数自体は固定しません。

## 実APIの証拠

[Wasm契約](module-contract.json)の7つの薄い関数が、本物のwasi_snapshot_preview1 importをcallします。JavaScriptはWASI環境の用意、Wasm export呼出し、線形メモリーの読取、記録だけを担当します。結果を返すmockやJavaScriptのファイル読取でWASIの成功を代用しません。fixtureの作成と終了後の削除はホスト側の準備・回収として分けます。

固定版のNode実体とmodule・sourceのSHA、完全な標準出力・標準エラー、呼出順、errno、成功した出力だけを保存します。正常な読出し、期待した拒否、未到達、準備失敗、実行失敗、後片付け失敗を分けます。1条件1子プロセスを逐次実行し、nice 10、各3秒・全体20秒以内。ブラウザーはこの実験に含めません。

## 原典と受入

sources内のuvwasi v0.0.23のfd_table.c/uvwasi.cと、公式WASI snapshot-01の型・APIを照合します。main/legacyへの404は取得記録に保持し、存在を独立確認したsnapshot-01へ変更しました。NodeのSecurity説明はSOURCE-MAP.mdに対応づけます。

手生成WasmをPythonで別decodeし、型・import・export・命令・データ・メモリー上限が手書き契約どおりか照合します。実行を始める前に独立担当が期待表と原典を確認します。保存した結果は別validatorで検証し、欠落・値改変・前の条件の結果の使い回しも検出します。画面は保存した実測のreaderで、新しいWASI実行とは呼びません。

一般的な隔離保証、WASI全体、clock/network、Component、他ランタイム、任意パス、実負荷性能は対象外です。元owner不明の共有元と全体台帳は変更しません。
