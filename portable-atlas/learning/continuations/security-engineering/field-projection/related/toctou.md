# Conditional read / TOCTOU — check時とread時は同じ所属？

合成SQLiteのdoc1をalphaとしてcheckし、別接続でbeta所属・BETA SYNTHETICへ変更commit後に読む。正常版はtenant条件単一SELECTで返却なし、故障版は旧checkを根拠にIDだけ再取得してbeta payloadを返す。固定順序の実SQL検証で、実並行raceや製品policyの証明ではない。

読む順は[元Subjectのobject認可](../../../subjects/security-engineering/README.md)（「次に学ぶ問いと小実験」policy/DBの整合・TOCTOU、line20） → [関連Identityのresource scope](../../identity-authentication-authorization/resource-scope-enforcement/README.md) → [Configの要求snapshot](../../application-configuration-feature-management/atomic-reload-snapshot/README.md) → [本UI](index.html)。元教材は不変memory、本単元は確認と使用の間に所属が変わるmutable storeを扱う。

前提はrequest/context、tenant、SQLite SELECT/UPDATE、transaction/commit。fixtureのactor-alpha/actor-betaは上流で認証済みのcontextという仮定で、各actorは所属tenant内read capabilityを持つ。認証・grant/role・複数table policyを実装しない。初期行はdoc1/alpha/ALPHA SYNTHETIC/revision1。beta更新はtenant/payload/revisionを同じwriter transactionで変更する。

観測起点は初期行commit後。2接続を専有tempDBに開き、reader `BEGIN→SELECT tenant→COMMIT`、writer `BEGIN IMMEDIATE→UPDATE→COMMIT`、readerの別 `BEGIN→SELECT→COMMIT` の順。確認と読取は同じsnapshot/transactionではなく、変更はread前に必ずcommitする。単一threadで順序を明示し、sleep、競合発生率、thread raceは使わない。各接続をcloseしtemp directoryをcleanupする。明示recordだけfinal DB snapshotを新runへ保存する。

正常版のprecheckは診断用であり、許可根拠ではない。`WHERE id=? AND tenant=?`を含むSELECTで現時点の所属を照合してpayloadを取得する。故障版は旧checkが許可なら`WHERE id=?`だけで取得する。変更なしは両版ALPHA返却、alpha→beta変更後は正常返却なし/故障BETA。変更をcheck前に済ませれば両版返却なし。beta actorで旧check deny後beta所属になれば正常は現条件でBETAを返し、故障は古いdenyで読取をskipする。alphaのままpayloadだけ更新した場合は両版が新payloadを読むので、tenant条件は古いpayload版固定や全失効保証ではない。

6観測条件・未知actor/型の3拒否・実SQL失敗1条件を[事前固定oracle](expected-table.json)へ列挙した。未知resourceは両版返却なし。入力拒否はSQL/変更なし・旧初期行を保持。SQL失敗は存在しないcolumnを実SELECTしてOperationalErrorを記録し、payloadなし、正常答え非表示。独立checkerはproducerをimportせず、固定interleaving/literal行/可否表と保存DBへの別direct SQLで照合する。SQL失敗条件で参照SELECTが返却可能でも、失敗したconsumerを成功と扱わない。

UIは保存原票reader。前提→予想→条件→正常/故障とpayload→check/commit/read境界→原典/実装/raw→答え。全予想選択肢で比較→答えを開く→予想だけ変更を検査する。新予想を保持し旧応答/trace/答え本文を空にしdetailsを閉じる。条件変更では予想も空にする。拒否時は初期行の対照を別表示し、成功後の実行失敗で旧payloadや答えを残さない。

```sh
PYTHONDONTWRITEBYTECODE=1 python3 checker.py
PYTHONDONTWRITEBYTECODE=1 python3 runner.py  # defaultはread-only checker
PYTHONDONTWRITEBYTECODE=1 python3 runner.py --record  # 明示fresh runのみ
python3 -u -m http.server 0 --bind 127.0.0.1  # 専有loopback、Ctrl-C終了
python3 route.py toctou-gap
```

[experiment.py](experiment.py)の実SQL/transaction flags/attempt/exit/error、10実DB snapshot、command/stdout/stderr/exit、fixture/oracle/source/artifact hashを明示runnerがfresh observationsへ保存する。通常checker/runnerは結果stdoutだけで全hash/mtime不変。[checker.py](checker.py)は固定表と別read-only SQL、5改竄対照を照合。[qa/README.md](qa/README.md)に実IAB・capture制限を保存する。追加依存は使わない。

[CWE-367](https://cwe.mitre.org/data/definitions/367.html)のDescription/Potential Mitigationsはcheck後の状態変化と保護境界を読む一次資料。教材の単一tenant SELECT、全失効、並行race、認証を保証する資料ではない。確認2026-10-05、URL/locatorを[sources.json](sources.json)へ保存し第三者本文を転載しない。

[coverage](coverage.json)は元READMEのTOCTOU実験を今回埋めた有限範囲と残りに分ける。未実行は実並行scheduleとisolation代替、grant/role失効、複数table policy、認証/session、distributed enforcement、全失効・製品安全認定。Skillは7入口/4除外の構造だけでモデル挙動未実行。元/他教材・Core/fullGate・Portalを変更せず、Subject/Atlas全体の完成、公開/commit/pushを主張しない。
