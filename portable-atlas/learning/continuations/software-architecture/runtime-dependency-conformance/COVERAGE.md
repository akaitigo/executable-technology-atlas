# 未教材と次の実験

元[Software architecture N2](../../../subjects/software-architecture/README.md)の有限view/conformance比較。元Subject・Portalは変更しません。

|未実証の問い|次の有限実験（未実施）|一次資料locator|
|---|---|---|
|別経路やreflectionでtraceは欠けるか|専用fixtureの固定getattr呼出しを追加し未観測の判定を比較|[Python sys.setprofile](https://docs.python.org/3.9/library/sys.html#sys.setprofile)|
|runtime図とdeploymentは何が異なるか|同じ固定use caseを2local processへ分け、通信traceと配置viewを明示|[C4 Dynamic](https://c4model.com/diagrams/dynamic)、[Deployment](https://c4model.com/diagrams/deployment)|
|source検査を拡げると何が拾えるか|固定from import/alias fixtureを増やしAST限定検査と実解決先を比較|[Python importlib](https://docs.python.org/3.9/library/importlib.html)|

全AST、未実行経路、一般DI framework、thread/async、reflection、実network/deploy、一般architecture適合は未実証です。trace欠落は適合の証拠ではありません。
