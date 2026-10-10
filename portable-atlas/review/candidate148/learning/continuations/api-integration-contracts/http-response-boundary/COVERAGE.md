# Atlas：JSONが読めても、応答が完全とは限らない

177教材を基準に、目標26の学習経路から元API README:20,37の未検証境界を選んだ。中心は、JSONとして完結した本文でもContent-Lengthの宣言に届かなければ完全なHTTP応答ではないこと、長さを指定したreadが例外を出さなくても受信完了の根拠にならないことである。

元API README:3,13–20とclient.py:18–38の実HTTP・媒体型・不正JSON・空本文・timeout、[前作のProblem Details](related.html?topic=problem-readme)の本文status判断は既存である。web-performance/encoded-decoded-body-budgetも実HTTPの本文長・圧縮前後・上限境界を扱う。今回の8192/8193byteも一般的な上限検査の別成果として再加算しない。作者による新教材加算は0とする。

読む順は、元APIの通信・契約 → 既存の本文長と上限 → 前作のProblem Detailsの意味 → 今回のframing（本文がどこで終わるか） → Skill。媒体型・JSONを再比較する旧5案は重複が大きいため採用せず、旧文章を `revisions/scope-to-framing/COVERAGE.before.md` に保持した。

[固定入力](cases.json)は、完全な105byte、宣言106byteに対して105byteで接続終了、8192byteちょうど、8193byteの4条件。すべて同じJSON objectに改行・末尾空白を付けた本文である。長さ不足と上限超過では後段JSON処理を実行しない。前作consumerの1024byte制限は変更せず、Problem member政策も再実装しない。

実HTTP受信は初回の1子で4条件を完了した。自己所有の動的loopbackポート1個・4回の逐次GET・各応答read(8193)を1回、nice10・15秒上限・再試行0を保存した。宣言106/受信105は無例外でもframingで拒否し、後段JSONは未検査・返却値null。8192は通過、8193は完全受信後に上限で拒否した。実importしたhttp.client/http.serverのSHAとPython 3.9.6を記録している。保存記録readerのGUIは4応答・10切替状態・5取得失敗/旧応答、8前提・6文書・遮断原典2件を確認した。実画面9枚を保存。最終独立受入は確認状態から辿る。[実施状態](qa/reader-acceptance.json)と[保存結果](observations/run-01/results.json)を分けて確認する。

未対象：timeout実測、任意の分割や切断原因、chunked/圧縮/重複Content-Length、TLS・認証・proxy・外部API、任意MIME/charset文法、全JSON/RFC適合性、業務副作用、再送安全性。今回の1byte不足は一般の通信障害診断ではない。受信できたJSONを業務成功とは呼ばず、分野全体の完了も主張しない。

根拠の正確な参照先は[SOURCES](SOURCES.md)、予測と受入条件は[CONTRACT](CONTRACT.md)へ。旧学習経路の「未実施」は現在の受入成果と照合し、ファイルが見つからないことを不存在の根拠にはしない。共有元・先行177教材は変更しない。

画面の到達範囲：1280×900/390×844の実viewport。狭幅の図・比較表は左右へ移動して読む方式で、全列の同時可視性は主張しない。原典への実ポインターと正確URLの要求は確認したが、GUI内では外部通信を遮断し公式本文は取得していない。
