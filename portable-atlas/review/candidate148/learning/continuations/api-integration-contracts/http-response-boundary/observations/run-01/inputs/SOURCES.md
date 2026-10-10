# Atlas：受信完了の規則と実装へ戻る

- [RFC 9112 §6.3 項6](https://www.rfc-editor.org/rfc/rfc9112.html#section-6.3)：Transfer-Encodingなしの有効なContent-Lengthと、宣言長に届く前に閉じた応答。今回の中心であり、任意framingへの完全適合は主張しない。
- [Python 3.9 HTTPResponse.read](https://docs.python.org/3.9/library/http.client.html#http.client.HTTPResponse.read)と[IncompleteRead](https://docs.python.org/3.9/library/http.client.html#http.client.IncompleteRead)：長さを指定した読取と例外のAPI。
- [CPython v3.9.6 http.client:408–468](https://github.com/python/cpython/blob/v3.9.6/Lib/http/client.py#L408-L468)：read(amt)はreadinto、read(None)は別経路。短い返却だけで必ずIncompleteReadを投げる実装ではない。今回、無制限readで別の結果を作らない。
- [RFC 9110 §8.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.3)と[RFC 9457 §3](https://www.rfc-editor.org/rfc/rfc9457.html#section-3)：媒体型とProblem Detailsは後段の前提。一般文法・全memberを再実装しない。

以上は2026-10-07に公式本文と固定版実装を実読した。Python 3.9文書の保守版とMacの実行版は同一と仮定しない。実行時Python版とimport元SHAは将来の記録へ分けて残す。

## 既存成果との差分



元Skillのルート直下artifacts参照を複製せず、実在する元evidence/run.json・evidence/artifacts.jsonへ導線を用意する。共有元はread-onlyのままとする。
