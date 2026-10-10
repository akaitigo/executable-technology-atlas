# Foundation Codable有限契約と検証範囲

実際に既存Swift 6.2.3 / Darwin arm64で[Lesson.swift](Lesson.swift)をcompile/runする。Foundation JSONDecoder、default key strategy、String `name`、Int8 `age`、String? `note`。domain上のageとして負数を推奨する仕様ではなく、Int8の表現境界を測る教材。

| field | 正常版の明示API | missing / null / 型違い |
|---|---|---|
| name | decode(String.self) | required。missing/keyNotFound、null/valueNotFound、数字など/typeMismatch |
| age | decode(Int8.self) | required。integer -128..127を表現。string/bool拒否、範囲外/小数部分あり拒否。整数値の7.0は今回実測対象 |
| note | decodeIfPresent(String.self) | missing/nullはnil、Stringなら値、型違いはthrow。optionalはあらゆる不正値をnilへ変える意味ではない |

`contains`/`decodeNil`を使えばmissing/nullを区別できるが、今回の正常Profileは両方をnilへまとめる。extra-keyはdefault keyed decodingで使われず、拒否validationを追加していない。top-level object以外/壊れたJSONは拒否。duplicate key、dates/Data/key strategy変更、深いnested JSON、JSON5、全数値表現、全decoderは検証外。

**意図異常2版:** `eager-optional`はnoteまでdecode(String)するためmissing/nullを拒否。`defaulting`は各fieldをtry?で読み、name失敗→空文字、age失敗→0、note失敗→nilへ隠す。root containerの失敗は隠さない。両版ともunsafe crashや強制unwrapを使わず、有限入力に対して実Swiftで比較。

18展示caseと160組のfield matrix検査、各raw JSONは小さいtext。runnerのcustom JSON入力は4096UTF-8byteまで。この上限は教材の有限化でFoundation制限ではない。[oracle](oracle.py)はPython標準JSON parserと独立type/range ruleでstatus/profileを予測。Swift実装をimportせず、raw結果から期待値を作らない。Swift error debug/pathは独立oracleが模倣せず、rawを保存し[手記anchor](hand-oracle.json)のmissing/null/type分類だけ別確認。Int8 overflowで今回dataCorrupted/path[]だった診断を全SDK共通の仕様とはしない。

**実行とread-only:** `observe.py --write-evidence`が既存xcrun swiftcを起動し、module内`.swift-task-*`一時directoryにbinary/module cache/TMPDIRを置く。標準入力で固定caseを渡し、終了コード・stdout・stderr・binary/input/source digestを保存し、TemporaryDirectoryで出力/cacheを除去。通常runnerは保存Swift観測のread-only再生、`--json`は明示表示されたPython oracle予測だけ。`--run-swift`を付けた場合に限り実compile/runと一時cache書き込み/cleanupを行う。通常checkerは再compileも原票更新もしない。

UIの「次の段階」は入力→name→age→note→結果の説明用段階表示。Swiftの内部実行step/時間計測ではない。表示するprofile/errorは実compile/runした保存出力。[原典](SOURCES.md)と実装を比較してから答えへ。

iOS app/device/simulator、Xcode project、他Apple OS、UI/actor/ARC/ABI/security/performanceは未実行。toolchain/SDK/license/OS設定の変更、package install、公開なし。
