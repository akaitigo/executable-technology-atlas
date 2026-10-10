# Atlas：今回扱う範囲

174受入後、目標26の次の一歩から選定。元APIの `client.py:12–38` は200/422・application/json・独自error.code/messageを扱う。元README:35のProblem Details比較はこの実装にない。既存retry-idempotencyは業務ledgerと応答喪失後再送の教材として差し引き、再加算しない。

今回の増分は、同じ伝送状態422に対する標準エラーのstatus省略/型違い/不一致と、type URIによる同一性。6応答×2consumer方針を実行して保存した。title翻訳・未知extensionも同じtypeの対照に限る。

対象計算1回は終了し、作者236照合・保存値8改変の検出と、独立担当243照合・6改変の検出を確認した。別にGUIの全12応答、10切替状態、5取得失敗・旧応答対照、前提7資料・文書6件の導線、実画面10枚を確認した。独立担当は表示値を1,454関係で照合した。各照合数は重複を含み合算しない。最終独立受入は[確認状態](qa/reader-acceptance.json)から辿る。入力schema拒否の実測は0例で、未測定の分岐まで成功としない。

未対象：実HTTP通信、proxyによる書換え、任意media文法/charset、相対type URI解決、URI参照先取得、全member/全status値/全schema境界、content negotiation、認証/TLS、業務副作用、retry安全性、一般RFC適合性。本教材の保留方針をすべての利用側への義務とはしない。

先に[元APIの契約](related.html?topic=api-readme)を読む。実際の前提本文は新readerの固定資料viewerへ接続し、旧Skillにあるルート直下artifacts.jsonを使わず実在するevidence/run.json・evidence/artifacts.json・sources.jsonへ結んだ。旧教材自体は編集していない。目標26全体の完了を示すものではなく、残る広い媒体文法や実通信の境界は今回の有限結果から推定しない。
