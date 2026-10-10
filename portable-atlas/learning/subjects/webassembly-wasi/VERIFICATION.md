# 検証記録

確認日：2026-10-05 JST。問いはi32.addとJS Numberの違い、拒否境界の区別。有限1教材だけの実証でありSubject全体はincomplete。旧Goalの完了や新Goal作成はしていません。Portal root Gate/Core audit・WASI・Component・全runtime互換性は未実行です。

## 実行原票

- [最終Node原票](observations/node-attempt-02/raw.json)：Node 25.2.1 / V8 14.1.146.11-node.14 / darwin / arm64、08:03:54.230–08:03:54.239 UTC。実WebAssemblyの12入力、84照合が成功。各run内のattempt1 / retries0を保存。
- [最終実Browser原票](observations/browser-attempt-02/raw.json)：IAB、UA Chrome 154.0.0.0 / Mac OS X 10_15_7 / ja / 1280×720、08:05:11.282–08:05:15.876 UTC。UAは実record値でありOSの独立probeではない。各runのtimestamp、API events、例外message、input、binary全hex/digest、source bindingを保存。
- [checker原票](observations/checker-attempt-02/raw.json)：08:05:27.861–08:05:27.883 UTC、881肯定照合・8負例拒否。負例で失敗前に成功した2723照合は別集計し881へ混ぜない。document local linkとE1–E4 roadmapも検査する。

Browser8操作：正常2+3、max overflow、bad magic、bad type、missing import、BigInt call、全12入力、Skill正常route2+3＋keyboard Enter。各観測にraw文字列/構造化raw、実UI cell/説明stack text、snapshot、実JPEGとhashを保存。画像保存機能を実確認し、overflow画像も実画素を目視確認。説明stackはengine内部Traceではない。

観測：成功8件・拒否4件・成功中のJS Number差5件。max+1→-2147483648、min-1→2147483647、max+max→-2、4294967295+2→1、小数3.75+1.25→4（JS Numberは5）。bad magic/typeはCompileError、import欠落はvalidate成功後にLinkError、正常i32 moduleへのBigIntはinvoke時TypeError。messageを実原票に残し、classだけの一致を全原因理解の証拠にはしない。

## 独立oracle・byteとsource binding

WebAssemblyを呼ばないBigInt modulo/signed算術で実返値を照合。bitwiseによるWasm模倣ではない。generatorとは別のliteral hexが各binaryの正確な同一性を固定する。実WebAssembly呼び出しはexperiment.mjsの経路であり、oracle返値を実行結果に代入しない。

|実体|byte数／SHA-256|
|---|---|
|正常module|41 / f61fd62f57c41269c3c23f360eeaf1090b1db9c38651106674d48bc65dba88ba|
|magic破損|41 / a6850745638e66ef30bc79c35f30106ee921729e38eedb7900993e80012a5337|
|type矛盾|41 / 437b0e539736fa9a6df7b476f916e8aab3e56517bd5dcfc97f055e06d309b21c|
|import要求module|39 / dfbaff3b3a4db185af8b6369720c52acf0db0d9f1794e12e0c156edb3889c79e|
|cases.json|5029dccd6ab2f088246bee4c1829161e4e6d6a6c856176d845a3e16d7ec0c5e9|
|Node raw|dbed1f882eb5e42e029e883cfaa4f205efec9e98698c0423cd16be1fdf64d280|
|Browser raw|b6da91f4fce7ccbb68c0d9796ef55c8e3ed0cada83a95c25f67f7bdfe0ddddd6|
|Node environment JSON|862f0a49149f5ccf6ff913a38ce1c93537e15f030700548b43382dc4b3ab2fa9|
|Browser environment JSON|4521642ec76f173eb6d2c9b50401573fbeae9296558eda542483f05cc8e85c8a|

environment hashは原票objectの`JSON.stringify`（キー順維持）をUTF-8でhashした派生識別子で、engine binaryのhashではない。Source集合はsources.mjsの13 member固定、generator/runner/oracle/checker/UI/Skillを含む。原票に全digestを保存。READMEと事後検証文書は説明としてSource集合の外だが、通常検査前後の全ファイル不変監査には含める。

8負例：wrapping結果の捏造、bad-type許可、import例外class混同、実byte改変、Sourceのdigest-only差替え、入力欠落、時刻欠落、説明stackの捏造。メモリ上cloneで検査し、成功raw/画像を消さない。

## 修正・保持・Skill・cleanup

[初回record失敗](observations/node-record-attempt-01/failure.json)はparent directoryがないENOENT。記録処理を修正して実Nodeを再実行した。初回個別Node終了値は未採取で、原票の推定exitCode 1を[訂正記録](observations/node-record-attempt-01-clarification/raw.json)で区別する（複合shellの実測終了値は0）。sandboxのlisten EPERMも[原票](observations/server-attempt-01/failure.json)で保持。どちらも時刻は未採取なのでnull、推測しない。通常host reviewを経た一時loopback previewのみ使用し、永続設定は変更していない。

WASI旧候補locatorが実取得で404だったため、取得できた公式WASI repositoryへ修正。Node/Browser/checker attempt01は旧Sourceの実履歴として保持し、最終Sourceでattempt02を実再取得。旧Sourceへ新digestを追記して新実行扱いしない。import module byte数は実測39と確認し文書も合わせた。

Skill quick_validate成功。正常routeは同一Agentが既存UIで2+3＋Enterを実操作、結果5。未対応routeのWASI/Component/全runtime保証はREADME E2/E3/E4へ案内し未実行を明示。routingの原票は同一Agentの案内記録、独立Forward Evalではない。

own tab13終了、own server session84443/39466はCtrl+C exit130。ports57312/57955のlistenerはlsof 0件/exit1。外部サービス、Docker、新依存、OS/GitHub設定、global install、commit/push/公開はなし。旧repoとPortal root文書、他教材の既存差分を保持。

最後に通常verify/check/Skill検査と既存directoryへのrecord拒否を実行し、前後の全ファイルhash一致をobservations/read-only-audit-01へ記録する。成功・拒否・失敗の原票は保持。WASI/Component/native各runtimeとE1–E4の未制作範囲はscope.jsonとREADME/indexで継続表示する。
