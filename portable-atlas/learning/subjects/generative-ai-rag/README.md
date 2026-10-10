# Generative AI / RAG — 検索した根拠と回答を結ぶ

対象分野をこのrepoから学ぶための入口。現在はretrieval→context→citation bindingの有限1単位。**生成モデルは動かしていない**。回答は著者が固定したfixtureで、検索と支持判定だけを実処理する。corpusは架空のarchive/garden案内4文書で、現実の施設情報ではない。

## 学習の道筋

1. **前提**：文字列、単語count、配列・ID、順位、集合、SHA-256を知る。検索文書、context、回答claim、citation、quoteは別々のデータである。
2. **主要概念・仕組み**：query語→lexical ranking→top-k→参照可能な全文章をchar budget内でcontextへ→固定著者回答→citation binding。scoreはqueryの異なる語について文書中出現数を合計。同点はdoc ID辞書順、score0は取得しない。
3. **今回実装・正常異常**：[視覚入口](index.html)で予想→操作→比較。[pipeline](pipeline.py)と[独立oracle](verify.py)でtraceと原票を確認する。
4. **実務判断**：citation IDの存在だけで支持を認めない。context内にあるか、参照資格があるか、原文quoteがあるか、claimがquoteと一致するかを分ける。context不足なら棄権を別結果として扱う。
5. **限界**：支持は固定の原文1文への文字列一致だけ。言い換え、含意、矛盾の一般判定、世界の真実、答えがqueryへ適切かを証明しない。文書種別は手動で、攻撃の自動検出器ではない。
6. **原典→次の学び**：[source binding](sources.json)と[coverage](coverage.json)を使い、ranking→chunk/budget→claim coverage→文書versionの4実験へ進む。

## 予想→操作→比較→原典/実装→答え

予想：citationが存在すれば答えは支持されるか。検索上位に命令文が来たら、それを操作の許可にできるか。検索済みでもcontextにない文を根拠にできるか。

module directoryで実行。Python標準ライブラリのみ、Mac直接、資格・外部API・新依存不要。

```sh
python3 verify.py
python3 serve.py --port 0
# 表示された127.0.0.1 HTTP URLを開く。終了はCtrl-C。
python3 route.py citation
python3 route.py llm-generation
```

操作：[UI](index.html)でcaseとstrict/citation-onlyを選び、traceを一段ずつ進める。UIは[実行原票](observations/raw.json)の説明用再生。ライブ検索・モデル生成・実時間性能測定ではない。

比較：strictは次の全条件を要求する。citation-onlyは意図的に存在条件だけを見る。

|条件|何を確認するか|
|---|---|
|citation_exists|corpusにそのIDがある|
|in_context|今回のcontextにその文書がある|
|reference_allowed|手動kindがreference。instruction-fixtureを根拠に昇格しない|
|quote_is_source_sentence|quoteが原文の完全な1文である|
|answer_matches_quote|claimがそのquoteと完全一致する|

|case|strict|citation-only|学ぶ境界|
|---|---|---|---|
|archive正常17:00 / garden正常08:00|受入|受入|原文1文とcontextを結ぶ|
|存在するarchive IDで23:00と主張|拒否|受入|ID存在と支持は違う|
|quote17:00だがclaim23:00|拒否|受入|正しい引用文でも誤った答えを支持しない|
|未知citation ID|拒否|拒否|存在しない根拠|
|garden contextでarchiveを引用|拒否|受入|corpus存在と今回contextを分ける|
|char budget0 / top-k0 / no match|拒否|受入|根拠欠落|
|instruction-noteを23:00の根拠に使う|拒否|受入|命令文を参照権限に昇格しない|
|contextなし、claims空|棄権|棄権|答えを捏造しないfixture|
|2claimの1つだけcontext支持|全体拒否|全体受入|claimごとのcoverageを確認|

原典/実装：[LewisらのRAG論文](https://arxiv.org/abs/2005.11401)は外部記憶からのretrievalと生成の結合を扱う。今回はdense index、neural retriever、seq2seq、fine-tuningを再現していない。[OWASP RAG Security](https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html)と[Prompt Injection Prevention](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)を、データ・権限・出力検査を分ける原典として読む。[pipeline](pipeline.py)のcontext段とbinding段へ対応させる。

答え：引用先が存在しても、23:00のclaimはarchive原文の17:00に支持されない。命令fixtureはlexical上位になってもcontextから除かれる。これは手動種別に対するローカル境界で、未知攻撃を見抜いた証拠ではない。citation-onlyは命令を実行する方式ではなく、誤った受入基準の比較方式である。全モードで文字列をデータとして扱い、eval・tool実行・外部送信はしない。

## Subject主要未教材coverage

[coverage.json](coverage.json)に概念・問いと公式locatorを対応させる。今回で理解できるのは検索順位、context容量、固定quoteの結合、棄権と参照境界。実生成や意味的faithfulnessは別に学ぶ。

|領域|次に学ぶ概念・問い|状態|
|---|---|---|
|生成モデル|tokenization、next-token、pretraining/instruction tuning、decoding。検索との違いは何か|生成モデル未実行|
|取得/chunk/index|parse、overlap、metadata、version、更新/削除。根拠が分断されないか|全文章の固定corpusのみ|
|retrieval/ranking|BM25、embedding、hybrid、rerank、query expansion。同義語で何が変わるか|単純lexicalのみ|
|context/prompt|LLM token budget、順序、重複、データ/命令分離。根拠を落とさないか|Python char budgetのみ|
|grounding/citation|span、claim coverage、entailment、矛盾、棄権。引用は答えを支持するか|literal1文のみ|
|評価|recall、ranking、faithfulness、正答性、human/judge bias。何を別々に測るか|固定oracle比較のみ|
|権限/攻撃|ACL、tenant、injection、poisoning、output処理。誰が参照/操作を許すか|手動kind境界のみ|
|会話/tool/agent|memory、permission、multi-step、structured output。根拠から実操作へ進めるか|未教材|
|運用/privacy/資源|latency/cost、cache、PII、provenance、更新/rollback。古い引用を失効できるか|未教材|

次の4実験（未実装）：①queryの同義語/反復を加えscoreと正規化を比較（[RAG原典](https://arxiv.org/abs/2005.11401)）、②chunk境界とoverlap/budgetの根拠span保持を比較（[RAG Security](https://cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html)）、③固定多claim・矛盾例で部分表示/全体受入/棄権を比較しliteralの限界を記録（同原典）、④同IDの2versionとallowlist変更でcache/span失効を比較（[信頼境界原典](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)）。

## 再現証拠と検査

[corpus](corpus.json)、[fixtures](fixtures.json)、[独立fact inventory](oracle-facts.json)、[raw](observations/raw.json)、[receipt](observations/receipt.json)を結合。receiptは実行UTC時刻・Python/OS/architecture・input/corpus/source/artifact SHA-256。原票は順位・matched count・context・除外理由・claim条件・source span・全traceを持つ。spanはPython文字indexの `[begin,end)`。

通常 `python3 verify.py` はread-only。更新だけ明示 `python3 verify.py --record`。独立oracleは本体tokenizerや判定器を呼ばず、文字scan/repeated maximum ranking、別のgolden fact inventoryとcontext予算で照合する。12case×2policy、全8参照fact、120個のseed固定query/budget変形、不正入力・corpus・option拒否、roadmap/local links/source bindingを検査。[Skill](skills/atlas-generative-ai-rag/SKILL.md)は既存checker/UIへ限定routeし、作者routing smokeを独立AgentEvalとは呼ばない。

[実IAB QA](observations/ui-qa.json)と[検証記録](VERIFICATION.md)はcapture保存可否・ownedresource終了を区別する。ASCII英数字token、corpus16文書以下、query200文字以下、top-k0..8、budget0..2048文字、8claim以下。日本語tokenization、embedding、モデル学習/生成、実LLM、安全保証、実製品RAGは未実装。この1単位から全Subject/Atlas全97入口の完成を主張しない。
