# Atlas — 原典と既存の学習経路

## 選定の根拠



## 公式本文から支える範囲

[OWASP AI Agent Security — Tool Authorization Middleware](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html#tool-authorization-middleware) と [High-Impact Action Integrity Controls](https://cheatsheetseries.owasp.org/cheatsheets/AI_Agent_Security_Cheat_Sheet.html#high-impact-action-integrity-controls) の本文を正式webで読取。取得参照turn130view0、前者271–273行、後者396–404行。2026-10-06の確認。

要点の独自要約：実行する側で具体的な操作と承認を照合する。操作主体、対象、引数、有効期間や使用状態が関係し、引数変更を元の承認で済ませない。観測された情報だけから承認を作らない。並行要求では照合と使用の原子性も別途必要になる。

本単元の2処理、JSON形式、hash規約、固定actor、論理期限10、逐次の使用フラグは教材固有の契約であり、OWASP規格への適合を意味しない。第三者本文は複製せず、この要約とlocatorを固定する。取得したHTMLのbyte hashは未採取。計算に使う固定契約・入力のhashと混同しない。
