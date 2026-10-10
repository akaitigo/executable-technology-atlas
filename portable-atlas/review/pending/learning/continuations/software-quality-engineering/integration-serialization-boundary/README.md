# 単体passとserialization境界

結果解釈 → 再現性と独立性 → unit外の統合境界へ進む教材です。既存Software Quality LEARNING_PATHの統合/E2E未教材から、小さなdelay_ms契約だけを切り出しました。直前のtest順/fixture、既存Software Quality、QEへread-only参照します。元教材と原票は変更しません。

独自domain契約はdelay_msのexact integer 1000/2000とfixture_id F1000/F2000、2キーだけ。fixture IDは相関用で、IDに値の意味を委ねません。正規serializationは整数msをJSONで保持。故障adapterは秒へ換算し文字列1/2を同じdelay_msキーへ入れます。

| serialization | receiver | 実HTTP | domain結果 |
|---|---|---:|---|
| normal | strict/coerce | 200 | 1000/2000msを保持 MATCH |
| seconds-string | strict | 400 | CONTRACT_REJECTED |
| seconds-string | coerce | 200 | 1/2msと誤受理 SEMANTIC_MISMATCH |

両端のpure domain単体testはどの条件でも実unittestでpassします。これらは正規domain値だけを検査し、adapterを含みません。単体passをHTTP統合passへ読み替えず、HTTP200も元の意味保持と別に照合します。strictの拒否とcoerceの誤受理を混同しません。

画面で予想→delay/serialization/receiver→実行→unit/wire/受信/意味の図→全attempt→source→答えを読む。1操作は実unit childと別のHTTP receiver childを起動し、同fixture IDの実POSTを2回行います。request/response UTF-8 bytesをhexでも保持し、receiver側の実読取bytesと照合します。全2 attemptを残し、よいretryだけ選びません。receiverは2 request後にclose/exitし、親は所有Popenだけを回収します。

`python3 -B verify.py`と`python3 -B route.py`は8条件×2実HTTP、15拒否、8集計mutantを照合し、新しいowned loopback childを起動します。sandboxがloopbackを拒否した場合はEXECUTION_INCOMPLETEであり検証成功ではありません。制作環境ではこのnetwork境界だけ既存のhost permission reviewで実行しました。再現には自身のloopback起動が許可された実行環境が必要です。record/sealで保存原票を上書きしません。

`python3 -B serve.py`の127.0.0.1動的URLを開きます。自身のserverだけCtrl-Cで終了します。追加package・実外部サービス・ホスト設定変更は不要。型拒否はdelay欄へtrue/1000.0/1等を入れて確認できます。5秒/3秒のprocess/HTTP終了上限は実timeout誘発の証拠ではありません。

手表は実装前にwire文字列と期待HTTP/domain値を固定。oracleはproducerをimportせず手表から比較します。core-sandbox-refusalは通信未実行の失敗、core-first-successは最初の8条件の実成功経路、attempt-01は制作時CLI全原票です。browser-casesは実DOMから照合したsemantic投影・PID/port/操作UTCの転記で、raw全文downloadではありません。保存されないcaptureに画像path/hashを作りません。source viewerは32768文字超を明示抜粋と全文リンクで示します。

RFC8259のJSON型/UTF-8とRFC9110のHTTP状態を参照しました。ms単位、有限許容値、400拒否の選択は独自契約で、標準に由来するdomain規則ではありません。Python http.server文書は3.9.25、実runtimeは3.9.6。教学loopbackを実運用serverへ広げません。全統合/E2E、実製品品質、HTTP/JSON全仕様、実ネットワーク障害、Core全体は未評価。
