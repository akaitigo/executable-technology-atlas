# ResourceTimingとHTTP bodyを分ける

[W3C Resource Timing](https://www.w3.org/TR/resource-timing/) を制作時に取得確認。2026-09-01 Candidate Recommendation Draft、§3.6のencodedBodySize/decodedBodySize getterと§3.5 cross-originをlocatorにする。両attributeはそれぞれencoded/decoded bodyのsizeを返す。cross-origin制限等でsizeが0になり得るため、0や欠測を測定成功へ置き換えない。

この単元は同origin固定body/no-store/unique URLだけ。header・TLS/TCP込みの実wire総bytes、latency、cache/CDN、一般圧縮率、WebVitalsを実証しない。仕様のtransferSizeを実wire測定と扱わず、本UIではbudget対象に使わない。

[元Subject](../../../subjects/web-performance/README.md)「未教材coverage」E2 network-loading/assets-budgetsのbody-size入口へ結合。[固定hex表](oracle.json)・[事前契約](EXPECTATIONS.md)・[配信](server.py)・[独立http.client生body/decode照合](oracle.py)へ戻る。gzip literalはこの実験の固定fixtureで、仕様から引用した圧縮例ではない。
