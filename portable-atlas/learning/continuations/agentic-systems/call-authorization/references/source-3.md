# Agentic systems — plan・tool・観測の権限を分ける

このrepoから対象分野を学ぶための入口。現在は固定planとdummy read/addの有限状態機械1単位。**AI推論・LLM自律動作・外部toolは実行しない**。planもtool resultも著者の固定fixtureで、real agent platformではない。

## 学習の道筋

1. **前提**：状態、遷移、整数、JSON、命令列、program counter（pc）、停止条件を知る。planを選ぶこととtoolを実行すること、戻り値を読むことは別の段階。
2. **主要概念・仕組み**：`START→PLAN→VALIDATE→EXECUTE→OBSERVE→PLAN`。明示endで終了、invalid/loop/budget/errorは別終端。tool allowlistと引数検査、planの出所は別の条件。
3. **今回実装・正常異常**：[graph UI](index.html)で予想→操作→比較し、[machine](machine.py)と[独立oracle](verify.py)を読む。graphとauditは実行済み状態列を再生する。
4. **実務判断**：tool名が許可されていても、tool result由来のplanは著者planの許可と同じではない。正常な数値やENDEDだけでpolicyを守ったと結論しない。停止原因を区別して、復旧・承認・再計画の判断へつなぐ。
5. **限界**：authored flagはこのtoy fixtureの出所で、実ユーザーの同意・OS権限・credentialの検査ではない。budgetはcommand回数で実時間timeoutや課金上限ではない。固定structured proposalを処理し、LLMへの攻撃検出を行わない。
6. **原典→次の学び**：[source binding](sources.json)と[coverage](coverage.json)を使い、typed result binding→call権限→idempotency→pause/handoffの4実験へ進む。

## 予想→操作→比較→原典/実装→答え

予想：read/addをallowlistにすればtool resultから来たplanも安全か。addまで済んだらendの予算は不要か。同じ状態へ戻るloopとtool errorは同じ終端か。

module directoryで実行する。Mac直接Python標準ライブラリだけ。外部API、資格、新依存不要。

```sh
python3 verify.py
python3 serve.py --port 0
# 表示された127.0.0.1 HTTP URLを開く。終了はCtrl-C。
python3 route.py budget
python3 route.py llm-agent
```

操作：[UI](index.html)でcaseとdata-only/promote-resultを選び、auditを一段ずつ再生する。現在の状態、edge、pc、steps、値、plan出所と呼出しを比較する。ライブ実行・実時間測定・LLM推論表示ではない。

- `read` はin-memory固定key counter/tainted/faultのみ。ファイル・ネットワーク・外部データを読むtoolではない。
- `add` は整数a,b（bool不可、各-100..100）のpureな和。永続データは変更しない。
- `jump` はtoyの制御命令で、toolではない。同じprogram/pc/last/sourceへの再訪を検出する。
- `end` はlast valueがある場合の末尾命令だけ。endにも1stepを使う。
- budgetは0..16、planは1..16命令。選択したcommandはinvalidでも1step。tool call数・audit edge数とは区別する。

比較：tainted readはvalue4と `proposed_plan=[add(4,100), end]` を返す。data-onlyは提案をデータとして無視し、著者planのadd(4,3)→endで7。bad variantは残planをtool-dataで置換し104。badも同じallowlistと引数検査を通るため、この差は未知tool拒否ではない。構造化データを意図的にplanへ昇格するコード上の誤りで、文字列のevalや外部の実操作はない。

|case|終端 / 値|判断|
|---|---|---|
|正常 / tainted data-only|ENDED / 7|著者planの順序を維持|
|tainted promote-result|ENDED / 104、authority_breach=true|allowlisted toolでもplan出所が変わる|
|unknown tool / invalid args / unknown key|REJECTED|dispatch前に拒否、tool callなし|
|loop|LOOP_REJECTED / 4|繰返し状態を検出。放置した無限実行ではない|
|budget2 / budget0|BUDGET_EXHAUSTED / 7または値なし|end未実行。計算済み7を完了結果と混同しない|
|end単独 / endの後に命令|REJECTED|不正な終了条件|
|readだけでendなし|MISSING_END / 4|明示end欠落|
|fault read|TOOL_ERROR / 値なし|意図したdummy errorで停止|
|jump範囲外 / command形不正|REJECTED|制御の入力拒否|
|add(100,100) / add(-100,-100)|ENDED / 200または-200|数値境界|

原典/実装：[ReAct論文](https://arxiv.org/abs/2210.03629)で推論/行動/観測の反復を学ぶ。今回はLLMがplanを生成・更新する実験を再現していない。[W3C SCXML](https://www.w3.org/TR/scxml/)で状態・遷移・終端を読み、今回のgraphへ対応させる。SCXML processorではない。[OWASP AI Agent Security](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)と[Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)でtool許可と出所の権限、観測と実操作を分け、[machine.py](machine.py)のVALIDATE/OBSERVE段へ戻る。

答え：allowlistは許可tool名の範囲を決めるが、tool resultへplan決定権を渡す根拠にならない。data-onlyでは提案から命令を選ばない。budget2では和7があってもendに到達していない。loop、予算不足、入力拒否、tool errorを別に記録して次の対応を決める。

## Subject主要未教材coverage

[coverage.json](coverage.json)の概念・問いと[公式locator](sources.json)を対応させる。今回から判断できるのは固定workflowの停止・型・tool名・出所境界で、自律推論や実運用の成功ではない。

|領域|次に学ぶ概念・問い|状態|
|---|---|---|
|agent/workflow・自律性|目標/観測/行動、model planner、plan repair、不確実性。固定planと推論はどう違うか|固定planのみ|
|tool/schema/dataflow|typed binding、structured output、外部接続。意図と引数の権限は揃うか|pure read/addのみ|
|状態/停止/制御|end/abort、budget/timeout、loop、cancel。何を上限にするか|command budgetと繰返し状態のみ|
|memory/context|会話、working/long-term、provenance、stale context、retrieval。保存情報を許可へ昇格しないか|未教材|
|権限/人の介入|capability、scope、approval、action integrity、least privilege。誰が実操作を許可するか|toy authored出所のみ|
|tool result/攻撃|data/instruction、indirect injection、output、poisoning。形式が正しければ許可になるか|固定proposal境界のみ|
|durable/復旧|retry/backoff、idempotency、checkpoint、compensation、resume。副作用を重複させないか|未教材|
|multi-agent|役割、handoff、共有状態、通信、競合。他agentの提案を誰の権限で採るか|未教材|
|評価/監査/運用|task成功とpolicy違反、failure taxonomy、privacy、cost/SLO。値が正しくても違反がないか|ローカルraw auditのみ|

次の4実験（未実装）：①typed result参照と欠損/型/cycleを比較（[Agent Security](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)）、②plan hash/call scopeとtool-data差替えを比較（[出所境界](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)）、③in-memory counter/operation IDでretry/checkpointを比較（[状態原典](https://www.w3.org/TR/scxml/)）、④固定pause/approve/cancel入力で再開位置・失効を比較（[人の介入](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html)）。

## 再現証拠と検査

[plans](plans.json)、[tools](tools.json)、[独立手動oracle](oracle.json)、[raw audit](observations/raw.json)、[receipt](observations/receipt.json)を結合。receiptはUTC実行時刻・Python/OS/architecture・input/tools/source/artifact SHA-256。rawは全edge、pc、steps、last value、出所、command、結果、拒否理由とtool callを持つ。hashは同じbytesの確認で、正しさ/実権限の証明ではない。

通常 `python3 verify.py` はread-only。更新だけ明示 `python3 verify.py --record`。独立oracleは本体tool/validatorを呼ばず、手動status/steps/value/call/pc予測と別transition表を照合。100個の固定seed直線planを予算ちょうど/不足で実行し、手計算と独立phase inductionを比較する。18case×2policy、不正トップレベル入力・option、roadmap/local links/source bindingも検査。[Skill](skills/atlas-agentic-systems/SKILL.md)は既存checker/UIへ限定route。作者routing smokeを独立AgentEvalとは呼ばない。

[実IAB QA](observations/ui-qa.json)と[検証記録](VERIFICATION.md)はcapture保存可否・ownedresource終了を区別する。LLMのreasoning trace、実agent性能、外部tool、実承認・credential、実MCP/SDK、多agent、攻撃防御保証は未実装。この1単位で全Subject/Atlas全97入口完成を主張しない。
