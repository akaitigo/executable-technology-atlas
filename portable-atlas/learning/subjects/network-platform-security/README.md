# Network / Platform Security

合成IPv4 packetを順序付きruleへ流し、first matchと意図的に欠陥のあるnaive any allowを比較する標準ライブラリ教材。[index.html](index.html) で予想→操作→packet flow比較→原典/実装→答えへ進む。OS firewall・iptables・nftables・security設定は変更しない。実packet filteringは未実行。

## 学習の道筋

1. 前提: IPv4の4octet、CIDRのprefix、TCP/UDP、port番号を知る。private addressは信頼できるidentityを意味しない。
2. 主要概念: ruleごとのsource/protocol/portのAND、一致ruleの順序、終端allow/deny、default deny、許可範囲の重なり。packet入力の拒否とpolicy上のdenyは別結果。
3. 今回の実装: [rules.json](rules.json) の4rule、[model.py](model.py) のstateless matcher。宛先address、interface、direction、connection stateは省略し、固定serviceへ向かう合成packetのsourceとdestination portのみを扱う。
4. 正常/異常: 信頼側のweb/admin/DNS許可、外側default deny、隔離側deny、/25と/24境界、port 0/65535、malformed address、naiveがdenyを無視する迂回を比較する。
5. 実務判断: 広い許可と狭い拒否の重なりは順序と停止条件を含めて検査する。allowを先に置く操作は単に表示を変えるのではなく、隔離側webも許可してしまう。許可表の意図を先に定め、matcherだけの自己一致で安全を断定しない。
6. 限界: 固定された教材方針の有限証拠であり、実ネットワークやhostの防御能力を証明しない。下のcoverageから次の問い・実験・原典へ進む。

## 実行

このディレクトリでPython標準ライブラリのみを使う。依存追加・Docker・実通信は不要。

```sh
python3 -B run.py --source 10.0.0.130 --protocol tcp --port 443 --order deny-first
python3 -B run.py --source 10.0.0.130 --protocol tcp --port 443 --order allow-first
python3 -B run.py --source 10.0.0.1 --protocol udp --port 53
python3 -B check.py
python3 -B server.py
```

serverが表示する127.0.0.1の一時port URLを開く。所有serverをCtrl-Cで終了。教材専用UI/APIのみ配信する。通常 [check.py](check.py) はread-only、原票更新だけ `python3 -B check.py --record` を明示する。CLI不正入力はJSON rejectedとexit 2、HTTPは400、UIは前回traceを消して入力拒否。policy denyは正常な評価結果でHTTP200。

## 固定権限表とrule

| source領域 | TCP 22 | TCP 443 | UDP 53 | その他 |
|---|---|---|---|---|
| 10.0.0.0–127 信頼側 | allow | allow | allow | deny |
| 10.0.0.128–255 隔離側 | deny | deny | deny | deny |
| 10.0.0.0/24外 | deny | deny | deny | deny |

これはdeny-firstの教材方針。10/8全体を信頼するruleではない。最初に10.0.0.128/25を全protocol/全port deny、次に10.0.0.0/24 TCP443 allow、次に10.0.0.0/25 TCP22 allow、最後に同/25 UDP53 allow。非一致はdefault deny。

naive matcherは一致denyを無視し、いずれか一致allowを採用する。隔離側TCP443はfirst=deny / naive=allowとなる。allow-firstではweb許可を先頭へ移すためfirstもallowになる。この順序変更は意図的に方針を壊す実験であり推奨設定ではない。

IPv4の文字列はIPv4Addressで解析し、leading zero・空文字・IPv6・hostnameを拒否。protocolはtcp/udpのみ。portはboolでない整数0..65535。0と65535は数値境界として受理するが、serviceが存在/到達可能とは主張しない。subnetの.0/.255も合成address値として検査し、実際にforwardされることを意味しない。ruleはstrict IPv4 CIDR、閉port区間、固有id、allow/deny/anyの限定形式で、1–8本。任意firewall言語のparserではない。

## 独立oracle・証拠・確認

[oracle.py](oracle.py) はmodel/ipaddressをimportせず、octet区分と固定permissions matrixで判定する。deny-first、allow-first、naiveの期待を別表に置き、10件の手計算境界表も持つ。checkは10.0.0.0/24全256値と外側8値、2protocol、代表境界port、2順序を走査し、raw decision trace、terminal停止、rule/input/raw digestを検査する。さらに全65536portを信頼側/隔離側の両protocolで走査する。有限入力範囲を明記し、全IPv4空間の網羅とは扱わない。

[evidence/run.json](evidence/run.json) に実行時刻/環境/command、入力、rule、grid比較のraw trace・全port比較のraw terminal decision配列、独立期待、input/raw/source digestを保存。[evidence/bindings.json](evidence/bindings.json) がsource/artifactファイルと一次locatorを結ぶ。[evidence/ui-qa.json](evidence/ui-qa.json) に実HTTP IABの観測とcapture取得/保存可否、所有server/tabのcleanupを記録する。実captureの未保存や未実行を成功へ読み替えない。

module内 [Skill](skills/atlas-network-platform-security/SKILL.md) は既存runner/checker/UIへだけroute。[routing-smoke](evidence/routing-smoke.json) は主agentの正常/未対応コマンド確認であり、独立forwardAgentEvalではない。Core `atlas audit` と `npm run gate` は専用module scope外で未実行。全Subject/Atlas完成は主張しない。新Goalは作成しない。

## 未教材coverageと次の実験

| 主要概念・問い | 次に作る実験 | 公式locator |
|---|---|---|
| 状態/経路/変換: 返信、conntrack、NAT、hook、複数chainで何を評価するか | 合成request/reply、NAT前後、accept後の別chain dropを比較 | [nftables manpage](https://netfilter.org/projects/nftables/manpage.html) のCONNTRACK、NAT、OVERALL EVALUATION |
| IPv6/fragment/ICMP: dual stackで穴を残さず必要な通信を許せるか | IPv6 prefix、fragment、ICMPの権限表と欠落を比較 | [RFC 8200 §4](https://www.rfc-editor.org/rfc/rfc8200.html#section-4) |
| identity/暗号: networkの位置だけで信頼できるか | 合成identity/resource/context方針とTLS証明書の期限/失効判断を別モデルで比較 | [NIST SP800-207](https://csrc.nist.gov/pubs/sp/800/207/final)、[TLS1.3 RFC8446](https://www.rfc-editor.org/rfc/rfc8446.html) |
| platform最小権限/運用: 通過後にprocessは何を操作できるか | 合成process権限表、監査event、policy変更とrollbackを比較 | [Linux Security Modules](https://docs.kernel.org/admin-guide/LSM/index.html) |

これらは未教材。実packet filter、OS hardening、TLS handshake、証明書検証、IDS/rate limit、性能・可用性・安全保証、攻撃traffic、実環境への適用は今回含まない。

## 原典と実装の対応

- [nftables公式manpage](https://netfilter.org/projects/nftables/manpage.html) のVERDICT STATEMENTS: 終端判断の原典。本教材は単一chainのallow/denyに限定。実nftablesではaccept後も他のbase chainでdropでき、jump/return等もある。本教材のfirst matchは実ruleset全体の完全再現ではない。
- [Python IPv4Address](https://docs.python.org/3/library/ipaddress.html#ipaddress.IPv4Address): 正規IPv4解析。source membershipはIPv4Networkで判定。
- [RFC1918 §3](https://www.rfc-editor.org/rfc/rfc1918.html#section-3): private addressの割当範囲。教材の信頼側/隔離側は独自方針であり、RFCの推奨ではない。

制作時に公式ページを実取得確認。初期候補Red Hatページとnftables wikiは取得失敗したため根拠に使用せず、取得できたNetfilter manpageを採用。原文全文は複製しない。
