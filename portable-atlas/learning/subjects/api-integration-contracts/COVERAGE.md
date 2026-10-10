# 有限教材の範囲

実HTTP denominatorは固定12 GET、同じowned loopback HTTP/1.1 server/client、1固定JSON契約です。分野全体のcoverage件数ではありません。

実行対象：compatible optional追加、required欠落、string/booleanへの型変更、exact status、Content-Type、malformed/empty JSON、custom error body、応答header前socket timeout、retry0、自己所有server終了。独立Oracleは固定wire/判定/gate列、保存検査はsource/Artifact digestへ結ぶ。

未教材と次の問いは[README](README.md)へ。retry/idempotency→応答喪失後POST再送、標準error→Problem Details比較、cache/conditional update→ETag/If-Match、byte framing/deadline→分割/途中切断/UTF-8/body上限の4本は未実施です。

その他主要未教材：外部API、実認証・authorization・TLS、pagination・rate limit、webhook・async delivery、API versioning/OpenAPI/JSON Schema全検証、proxy/cache/HTTP2/3、SLO・負荷・production運用。本文内の簡単な図は観測の説明用で、packet captureではありません。分野全体未完成。
