---
name: atlas-conditional-read-toctou
description: 固定SQLite scheduleでtenant条件SELECTと旧check後ID-only読取を比較する。認証、実並行race、全失効、製品policy保証には使わない。
---
README・contracts・fixed oracleを読み、route.pyの7入口へ対応づける。予想→check/変更commit/read→payload非返却対照→SQL境界/原典→答えを辿る。
観測起点は合成初期行commit後。reader check transactionをcommitし、別writerの変更をcommitしてから別reader read transactionを開始する。明示順序は実並行race検証ではない。
正常precheckは診断用で許可根拠に使わず、現tenant条件と取得を単一SELECTにする。故障は旧check許可ならIDのみ取得。認証済みactor contextは仮定でfixture内tenantだけを検証する。
未知actor/型はSQLなし拒否、旧行対照は保持。SQL OperationalErrorはpayloadなし・正常答えなし。全予想単独変更では新値保持、旧比較/trace/答え本文を空にしてdetailsを閉じる。
通常checker/runnerは全hash/mtime不変、stdoutだけ。明示再記録だけrunner --recordでfresh snapshot/receiptを作る。専有tempDBと2接続を終了し所有tmpを除去する。UIは保存readerでSQL再実行ではない。
CWE-367はcheck/use境界の参照で、この独自tenant policyの証明ではない。実認証・全失効・並行race・製品policy・外部DB・権限/公開/課金は除外しREADME残coverageへ案内する。
