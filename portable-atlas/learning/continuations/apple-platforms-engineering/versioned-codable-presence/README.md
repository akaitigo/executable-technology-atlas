# version付きCodable：欠落と明示nullを分ける

[元Subject](../../../subjects/apple-platforms-engineering/README.md)のoptional/type/error → [COVERAGE次1](../../../subjects/apple-platforms-engineering/COVERAGE.md)のnested schema → 本教材 → [Migration expand/contract](../../software-maintenance-migration/expand-contract-client-coexistence/README.md)の順に読む。schema値の移行成功と旧client廃止/互換性の境界は違います。SQL移行を本Codableへ実装したわけではありません。前提はSwift Optional/throws、JSONobjectとkey、Codable/CodingKeys、compileとrun。UIは予想→実Swift処理→比較→原典/実装/raw→答えです。

## 独自方針と固定表

rootはversion、profileはname:StringとdisplayName:String?。v1のdisplayName欠落だけnameへ補完し、明示nullは保持。v2はkey必須・null可。数値をStringへ変換せず型拒否。未知version99は拒否。accepted入力はv2へencodeし、nilはencodeNilでkeyを明示。再decodeは故障modeを渡さないstrict v2です。

| version / displayName | strict結果 | fallback故障対照 | v2 encode / 再decode |
|---|---|---|---|
| v1 / missing | Akiへ補完 | 同じAki、matching control | keyありAki |
| v1 / null | nil保持 | Akiへ潰す、違反 | strictはkeyありnull |
| v1 / String Mika | Mika | 未採取 | keyありMika |
| v2 / missing | keyNotFound | Akiで誤受入 | 故障のroundtrip成功は元契約違反 |
| v2 / null | nil保持 | Akiへ潰す、違反 | strictはkeyありnull |
| v2 / String Mika | Mika | 未採取 | keyありMika |
| v1/v2 / number7 | typeMismatch | 未採取 | encode未実行 |
| version99 / String | dataCorrupted UNKNOWN_VERSION | 未採取 | encode未実行 |
| v1 / null＋future未知key | null保持、future無視 | 未採取 | futureは出力へ保持されない |

14条件：strict roundtrip6、期待decode拒否4、故障契約違反3、故障matching control1。decodeIfPresent ?? nameはmissing/nullの両方をfallbackにする故障対照。missingの一致だけでnull保持やv2必須keyを保証しません。未知keyはroundtripで消えるので全JSON保存ではありません。

containsで存在確認、存在時だけdecodeNilでnullを区別、非nullだけString decode。custom CodableはnestedContainer/CodingKeysを使い、nilをencodeIfPresentではなくencodeNil。Swift内部のstep traceを合成せず実presence/値/encoded JSON/再decode/診断を比較します。

## 独立oracle・compile/run・原票

fixturesとhand-oracleのversion×存在×型×期待値はSwift採取前に固定。oracle.pyはPython jsonで入力を分類して固定表を選び、Swift decoder/移行関数を共有しません。checkerはencoded_textをJSON objectとして比較し、文字列整形/key順を正しさの基準にしません。

初回observations/20261005T140900115392Z/raw.jsonはcompile/process exit0でしたが、未知versionの診断path事前予想[]と実["version"]が不一致。initial-hand-oracle.jsonとhand-diagnostic-failure.jsonに初回表・exit1・実差分を保持。keyを含む診断期待だけ修正し、新attempt observations/20261005T140958052012Z/raw.jsonを採用。semantic移行期待は不変です。checkerは旧handのexact SHA snapshotも照合し、2原票を現在の明示診断期待/独立値表で検査。過去原票を上書きしていません。

Apple Swift6.2.3、arm64-apple-macosx26.0、Foundation/macOS command line。既存swiftcの実compileとbinary SHA、command/UTC/exit/stdout/stderr/toolchain、実process input/stdout/stderr/exitを保存。contract拒否はprocess exit0のresultで、compile/process失敗と別です。binary/module-cache/TMPDIR/CLANG_MODULE_CACHE_PATH/SWIFT_MODULECACHE_PATHは自身の/private/tmp ephemeral directoryへ限定し各record終了後cleanup。binaryは配布せずhash保持。private absolute pathはOWN_TMPへ置換します。

このdirectoryで:

~~~sh
python3 -B check.py
python3 -B skills/atlas-versioned-codable-presence/route.py codable-presence
python3 -B runner.py --case v1-null
python3 -B runner.py --record
python3 -B server.py
~~~

checker/Skill routeはSwift再compileをせず全ファイルSHA/mtime不変。6改変を拒否。runner --caseは明示実compile/runで保存せずtmp cleanup、--recordのみfresh保存。UI serverは自身のtmpへ一度compileし、各clickで実binaryをdecode/encode/redecode。rawでは稼働中tmp未cleanupを明示しshutdownでcleanupを別確認。元/他Subjectをruntime依存にしません。

## UI検証・失敗境界

case変更は3予想unknown。各予想だけ変更は新値を保持し比較/表/trace/rawを消し、答え本文を空にして閉じます。run-startも同clear、generationで旧応答を破棄。各予想QAは「比較→答えを開く→予想だけ変更」で本文空/閉鎖を実IAB確認。拒否とEXECUTION_FAILUREは別、失敗はphase/error/未確認で旧正常答えを残しません。

QA previewのsynthetic返却失敗/HTTP503/保留応答は実Swift/Foundation障害と混同せず正常binary実行と区別。actual IAB captureが表示のみならローカル未保存と記録し再構成画像を作りません。sandbox bind拒否を保存し同serverのhost許可を使用。所有tab/port/tmpだけ終了します。

## 原典・実務判断・未教材

2026-10-05、一次資料[Swift公式Codable.swift](https://github.com/swiftlang/swift/blob/main/stdlib/public/core/Codable.swift)と公式rawのcontains/decodeNil/encodeNil/decodeIfPresentを確認。null keyでもcontainsは存在を表し、decodeNilは欠落でkeyNotFoundをthrowするので存在確認を先にします。main locatorと既存binaryが同revisionとは保証しません。文章/コード/図を転載せず独自schemaを実装。

欠落/null/default/型不正/version拒否と出力key/値の契約を先に決めます。roundtrip成功だけで入力全情報や旧client互換性が保存されたとは言えません。iOS UI/端末/simulator、全JSON/duplicate keys/深いnest/date/Data、任意malformed input、SDK間互換/ABI、署名/配布/entitlement、actors/ARCは未実証。設定/install/新repo/課金/公開/権限/Core/fullGate/commit/pushは未実施。Subject/Atlas全体未完成。

次の未実施案3本：①未知key bagを保持する契約、②旧/new clientのv2互換matrix/contract条件、③既存対応SDK別の同JSON/error/path/key存在の追試。現在は単一Mac toolchainと14固定入力のみです。
