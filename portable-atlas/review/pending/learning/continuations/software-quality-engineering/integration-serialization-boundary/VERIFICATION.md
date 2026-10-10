# 実経路と証拠

hand-oracleは実装前に2fixtureのexact wireと4組のHTTP/domain期待値を固定。oracleはdomain/modelをimportせず、wire bytes/hex、両端unit result、unit stdout/stderr、実client response、receiverが読んだrequest/response bytes、owned child close/exitを比較します。

unit_workerはstdlib unittestでcanonical sender/receiverを実行し、serializerを検査していない範囲をrawへ明記。receiver_workerは127.0.0.1動的portのHTTPServerを別processで起動し、2POSTの後にclose/exit0。親はHTTPConnectionで実送受信し、stdout/stderr/exitを保持します。所有Popen以外を停止しません。

8条件・各2 attempt、15拒否、8mutantを検証。unitからE2Eを誤推論、wrong wire/type/unit、拒否attempt隠し、HTTP状態混同、receiver bytes不一致、fixture ID変更、child閉鎖偽称を拒否。保存原票と新実行のsemantic一致を確認し、PID/port/UTCを固定値扱いしません。

core-sandbox-refusalはbind拒否をEXECUTION_INCOMPLETEとして残し、core-first-successはhost permission review後の別実行。rawの失敗を上書きしません。UI authoring helperは初回と再試行のNon-UTF-8 SyntaxErrorを保存。strict UTF-8 decodeは成功して原因未確定、短い行とencoding宣言で再生成に成功しました。これはHTTP技術検証成功ではなく制作経路の失敗/復旧です。RFC9110の最初の取得Internal Errorはsources.jsonに残し、公式HTTPWG publicationで復旧しました。

attempt-01は全CLI child/HTTP原票、initial-receiptは初期source receipt、receiptはUI後のsource/証拠を封印。browser-casesはsemantic全項目と操作UTC/PID/portの圧縮転記で、browser raw全文取得ではありません。再検証では新しい全8条件を実行するが、readonlyなので原票へ追記しません。

最後にverify/route/Skill/private-path検索の前後SHA256/mtime_ns不変を確認し、proofを最後に書きます。localhost network permissionが必要な再検証と、filesystemを変更しないことは別です。全Core gateは未実行。既存3 listenerは保存、専用UI server/tabだけ終了します。
