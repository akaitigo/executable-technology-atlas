# 原典と実証

2026-10-05に[PEP3333 Input and Error Streams](https://peps.python.org/pep-3333/#input-and-error-streams)およびstart_response本文を確認。wsgi.inputはrequest bodyのbyte stream、wsgi.errorsはerror用text stream。CONTENT_LENGTHを超えて読むべきでなく、appはserverのinput/errorsをcloseしない。この単元はbounded read(size)、errors.write/flush、start_response(status,headers)、bytes iterableへ対応付ける。

[adapter](adapter.py)の400/500等へのmapping、units契約、fault headerは教材独自。WSGI全仕様適合、framework DI、TLS/concurrency/streaming後例外の証明ではない。[実raw pointer](evidence/current.json)、[literal oracle](oracle.json)、[独立SQL検証](oracle.py)で対応を確かめる。

[Python wsgiref](https://docs.python.org/3.9/library/wsgiref.html)、[HTTP client](https://docs.python.org/3.9/library/http.client.html)、[sqlite3](https://docs.python.org/3.9/library/sqlite3.html)は再現APIのlocator（今回本文未取得）。[SQLite transactions](https://www.sqlite.org/lang_transaction.html)は前教材と次の競合検証locator（今回本文未取得）。
