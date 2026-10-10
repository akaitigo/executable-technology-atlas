# 一次資料と実証範囲

2026-10-05に[OpenTelemetry Context Propagation](https://opentelemetry.io/docs/concepts/context-propagation/)のContext、Propagation、Custom Context Propagation本文を確認。送り手がcarrierへcontextをinjectし、受け手がextractすること、同じtrace IDと親spanの指定で操作を関連付ける概念に対応する。

今回のcarrierはローカルstdin JSONの独自field。公式Propagators API、SDK、W3C traceparent適合、HTTP/実network、backendは実行していない。hex桁数を似せても公式適合の証明にはならない。

[Python subprocess](https://docs.python.org/3.9/library/subprocess.html)は次のprotocol/timeout追試locator（今回本文未取得）。[OTel Traces](https://opentelemetry.io/docs/concepts/signals/traces/)と[Sampling](https://opentelemetry.io/docs/concepts/sampling/)は次単元locator（本文未取得）。原典本文の転記ではなく、[実装](child.py)、[事前契約](EXPECTATIONS.md)、[手書きoracle](oracle.json)、[保存raw pointer](evidence/current.json)へ戻って実証の範囲を判断する。
