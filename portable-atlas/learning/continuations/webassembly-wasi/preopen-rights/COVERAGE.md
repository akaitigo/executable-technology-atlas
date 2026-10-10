# Atlas：WASI教材の対応範囲

分野目標22の「WASIの権限とホスト資源の境界」、既存学習経路E2のうち、事前ディレクトリとファイル読取りを扱います。全知識の網羅や教材数は到達目標にしません。

| 概念 | この教材の根拠 | 残る境界 |
|---|---|---|
| preopenを渡す | なし/ありの実WASI照会 | 複数preopen・別runtime |
| FDとrightsの違い | BADF 8とNOTCAPABLE 76 | FD再利用・権限の一般設計 |
| baseとinheriting | baseのPATH_OPENだけ減少 | 開いたfile FDのFD_READ減少 |
| 許可内の名前欠落 | NOENT 44 | symlink・外部パスは実験しない |
| 成功時の出力・EOF | 返却FD、6bytes、後続0bytes | 大容量・部分I/O・非同期 |
| 資源回収 | guest close、子終了、fixture削除 | runtime故障時の実注入は未実施 |
| バイトと型 | 独立decode、実装前契約 | 一般Wasm検証器ではない |
| Nodeの隔離境界 | 固定版公式Security | untrusted用途の安全性保証なし |

実行ログ・生成準備失敗・取得404・優先度変更拒否は区別して保存しました。実測後guardの動作は関数注入だけで確認し、新たなWASI実行はしていません。画面の欠落/改変/別条件表示拒否は、WASIの権限拒否とは別の確認です。

既存Core i32/JS APIとmemory.grow単元、および127＋独立15の範囲を読取照合した記録は `scope-review.json` にあります。Core成功をWASI実測として流用していません。元ownerの現在状態は未確認で共有元を編集せず、全体台帳と統合は担当外です。ここでは教材数を加算しません。

次の不足は「開いたfile FDのFD_READを減らす条件」と「ディレクトリのinheritingが要求rightsを満たさない条件」の分離です。現在の4条件から未観測結果を断定せず、別の契約・独立期待・自己所有fixtureが必要です。clock/network/Componentや他runtimeはさらに別の前提が必要です。
