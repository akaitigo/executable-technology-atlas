# runtime dependencyと責務適合 — 同じcore→adapter業務辺でも判定は同じか

専用4fixtureを独立childで実行します。root通常import+DI、root動的import+DI、core直接import+生成、core動的import+生成。業務runtime辺core.perform→adapter.Adapter.addと出力5は全case共通で、これ自体を禁止辺として扱いません。

## 前提と読む順番

Python 3.9以上の標準ライブラリ、関数/class、ASTのImport/ImportFrom、DIが前提。pipや外部serviceは不要です。

1. [元Software architecture Subject](../../../subjects/software-architecture/README.md)の依存図の限界とN2を読む。[元worker](../../../subjects/software-architecture/worker.py)のadapter選択・生成と[domain](../../../subjects/software-architecture/domain.py)の注入port呼出しを分ける。
2. [事前literal oracle](oracle.json)の固定source・import辺・caller/callee・出力・責務表で予想する。
3. [UI](index.html)でroot-static→root-dynamic→core-static→core-dynamic→trace-off→拒否/実行失敗を比較。
4. [worker](worker.py)の実profile観測と[policy](policy.py)の独自判断、[checker](checker.py)の独立手表を分けて読む。
5. [Cloud read教材](../../cloud-architecture/replica-lag-failover-read/README.md)でavailable/freshnessの観測と独自契約の分離を比較し、[未教材](COVERAGE.md)へ。

## 独自契約 → 予想 → 操作

具体adapterの選択・生成はcomposition rootの責務。coreによる注入portのadd呼出しは許可します。root側で選択/生成する1/2はCONFORMING、core側で行う3/4はRESPONSIBILITY_VIOLATION。一般architectureの必須規則ではなく、この教材の固定契約です。

ASTは3sourceのImport/ImportFromだけを抽出。1 root→adapter、2 root→importlib、3 core→adapter、4 core→importlibが該当辺です。全caseのroot→coreも抽出します。import_module引数の動的先はこのAST検査では抽出しません。

専用childのsys.setprofileでPython call/return、実caller/callee module/function、Adapter.__init__、Adapter.addの引数/return、importlib.import_moduleのrequested/resolved moduleを採取します。固定fixture名4件、動的moduleは固定adapterだけ。任意moduleを指定するrequestはimport前に拒否します。元Subjectをruntime依存にしません。

判断はfixture名やprofile labelではなく、実constructor callerと動的選択caller・trace完備性を使います。trace-offも実業務出力は5ですが判定不能。部分的にconstructor/動的解決traceが欠ける対照でも、同じ業務辺が残っているだけで適合を推論しません。観測とpolicy判断はraw内で分離しています。

~~~sh
python3 -B runner.py --record  # 明示更新：新UTC runのみ作成、旧raw保持
python3 -B checker.py
python3 -B test_negative.py
python3 -B route.py inspect
python3 -B route.py lesson
python3 -B preview.py
~~~

previewの動的127.0.0.1 URLでAST具体辺・constructor caller・責務判定を予想して比較。条件変更は予想をreset。各予想単独変更は新予想群を保持し旧比較・答え・trace・rawを消します。別terminalのpreview終了はCtrl-C。配信は専有moduleと指定の元/関連READMEのみで、参照欄に原本本文を読み取り表示します。

[CURRENT](CURRENT)のrunに実UTC/環境/input/exit/stdout/stderr/source・artifact hashを保存。通常runner/checker/routeは読み取り専用。[QA](QA.json)に実IAB・capture・hash/mtime不変・専用資源終了を記録します。

## 比較 → 原典 → 実装 → 答え

|fixture|Import限定ASTの該当辺|実constructor caller|実動的adapter選択|業務辺/output|独自契約判断|
|---|---|---|---|---|---|
|root-static|root→adapter|root.run|なし|core→adapter.add / 5|適合|
|root-dynamic|root→importlib|root.run|root.run→import_module→adapter|同じ / 5|適合|
|core-static|core→adapter|core.perform|なし|同じ / 5|責務違反|
|core-dynamic|core→importlib|core.perform|core.perform→import_module→adapter|同じ / 5|責務違反|
|4fixture各trace-off|ASTは上と同じ|未観測|未観測|出力5、業務辺は未観測|判定不能|
|allowlist外request|未観測|未観測|未import|exit2拒否|判定なし|
|malformed JSON|未観測|未観測|未実行|exit3/stdout空|EXECUTION_FAILURE、正常答えなし|

[C4 Dynamic diagram](https://c4model.com/diagrams/dynamic)は特定use caseのruntime協調を順序付きで表す観点、[Python importlib.import_module](https://docs.python.org/3.9/library/importlib.html#importlib.import_module)は動的module解決、[sys.setprofile](https://docs.python.org/3.9/library/sys.html#sys.setprofile)はcall/return観測の一次資料です。教材の図は限定source import viewと順序付き実trace viewで、正式なcontext/component/deployment全図ではありません。独自責務policyをC4/Pythonの規則と同一視しません。

[checker](checker.py)はproducerをimportせず、固定4source、AST辺、順序付きcaller/callee、出力5と手書き責務表を照合します。raw/派生値/hashを一緒に改ざんする8負例と、部分trace欠落2対照を検査します。

答えは同じ業務runtime辺があっても生成・選択の責務は別、です。動的importだけで違反とは判断せず、root動的importはこの契約では適合。core直接生成は業務出力が同じでも責務違反です。traceがない場合は判定不能で、業務出力一致やDI labelから適合を補いません。実行失敗で正常答えを補いません。

## 実務判断と限界

レビューではsource依存、実callee/caller、具体技術の選択/生成、契約判定を分け、観測していない経路を図の空白として扱います。全Subject未完成。全AST/全経路、未実行reflection、network/deployment、C extension、thread/async、動的module全種類、一般architecture適合は未実証です。[次の実験](COVERAGE.md)を参照してください。
