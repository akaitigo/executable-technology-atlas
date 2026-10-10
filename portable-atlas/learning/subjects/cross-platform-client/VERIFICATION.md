# 検証記録

実行日：2026-10-05 JST。有限教材だけの検証であり、Subject全体・旧Goalは未完了。Portal root Gate/Core auditはこの有限作業では実行していません。旧FE repo、既存の他教材、root README/docsは変更していません。

## 実測と独立照合

- [Python最終原票](observations/python-attempt-04/raw.json)：CPython 3.9.6 / Darwin / arm64、07:43:50.308173–07:43:50.311075 UTC。13入力、7 fieldずつ91照合。実stdlib len/encodeを使用。外部ライブラリなし。
- [Browser最終原票](observations/browser-attempt-02/raw.json)：IAB / UA Chrome 154.0.0.0 / Mac OS X 10_15_7 / ja / 1280×720、07:44:49.300–07:44:52.650 UTC。UAは実recordの値で、実OSの独立probeと混同しない。
- [checker最終原票](observations/checker-attempt-02/raw.json)：Node 25.2.1実行、07:45:26.898–07:45:26.914 UTC。肯定・負例照合中の693 assertion成功（負例で例外前に成功した照合も含む）。7負例を全て拒否。checker自身もSource memberへ含める。

BrowserはASCII4、emoji3、emoji4、孤立surrogate、全13入力、Skill正常routeのemoji2＋Enterの6操作。各操作の時刻、raw文字列、構造化raw、画面snapshot、table cell値とJPEG hashを保存。checkerはrawと実UI cellの両方を独立oracleへ照合する。画像も実ファイルhashを検証する。

観測：emoji3はUTF-16=6 / codepoint=3 / UTF-8=12。旧JSは拒否、旧Pythonは許可、共有コードポイント契約は両方許可、byte契約は両方拒否。emoji4でも旧判定差があり、全13の差はこの2件。空文字・超過・孤立surrogate・非stringは契約どおり拒否。codepoint数を表示文字数へ転用しない。

7負例：codepoint誤記、byte単位混同、Source stale、vector欠落、Python Artifact digest捏造、実時刻欠落、不正surrogate許可。負例はメモリ上のcloneだけを変え、成功原票を保持する。

## Binding

Source集合は[sources.mjs](sources.mjs)の13 member固定。入力/Oracle/JS/Python/UI/Skill/server/checkerを含み、directory globで変動させない。各最終原票へ実SHA-256を保存。

|実体|SHA-256|
|---|---|
|入力 vectors.json|ed502c89a56e788c90df8ee1bd8138b226ab842c8d5eed568dfafc787fd57c2f|
|Python raw|a963ca7a757fcee3eefa49955f87ff0c000dadc3137612d62bc12fabb069687d|
|Browser raw|dc243efbcaea411a704384568485f1582b9bb4c9a0feeb7ca17f0b609fc3576d|
|Python environment JSON|c22da48ad02024a971ff8dfc5436812567d17e5ecdb236bcb5d26d0326a42d66|
|Browser environment JSON|4521642ec76f173eb6d2c9b50401573fbeae9296558eda542483f05cc8e85c8a|

environment digestは原票のenvironment objectを`JSON.stringify`（キー挿入順維持）しUTF-8でhashした派生識別子。Runtime binaryのhashではない。README/この検証文書は事後の解説で実行Source集合に含めず、通常チェックの全ファイル不変監査には含める。

## 保持とSkill

Python attempt01–03、Browser attempt01、checker attempt01は実行した旧Sourceの履歴として保持。実UI cell照合・Skill手順・学習経路を追加した後、PythonとBrowserを最終Sourceで**実再実行**した。旧原票のSource digestを追記更新して新実行とは呼んでいない。

server attempt01はsandboxのlisten EPERM。[失敗原票](observations/server-attempt-01/failure.json)は時刻未記録をnullとし推測しない。通常host reviewを経た一時loopback previewのみ起動し、永続設定・外部公開なし。

Skill quick_validate成功。同一Agentの正常routeは実UI emoji2＋Enter。未対応routeはnative全OS保証を主張せずREADME E1へ案内。原票のskillRoutesは同一Agentの案内記録であり、独立Agent Forward Evalやnative実行ではない。

own tab12を終了。own server session47189/93984/8963/61320をCtrl+Cで終了（exit130）。ports55640/55792/55892/56096のlistenerはlsofで0件、exit1。Docker・他task process・volume・global cacheに触れていない。commit/push/公開なし。

通常チェックと既存directoryへの--record拒否の前後で全ファイルhashの一致を確認し、結果をobservations/read-only-audit-01へ追加する。更新は明示的な未使用directoryへのrecordだけ。全Subject完成・native実行・外部AT/Cloud/HIL・独立Forward Evalは未達のまま。
