# Security / Privacy

- Telemetry、Cookie、外部Font、外部Scriptを使用しない。
- Importerはローカルartifactまたは明示された固定Releaseだけを受け付け、URLを実行・追跡しない。
- 署名とDigestをSchema解釈前に検証し、不一致は隔離する。
- Manifest内のcommandは表示対象であり実行しない。
- CSP、Referrer Policy、Permissions Policy、frame拒否を`public/_headers`で配布する。
- Fixtureの秘密鍵は実鍵ではなく、決定論的なtest-only seedから生成する。Trust Storeにも`fixture-only`を明記する。
- Authority Review export/packetは一次資料本文を保存せず、HTTPS URL、locator、offset、SHA-256 bindingだけを保持する。Portalは外部本文を代理取得せず、利用者が一次資料を直接開く。`write_decisions=false`を固定し、Reviewer情報やDecision候補を保存・送信しない。
- Authority Reviewの遅延読込はexportとpacketの取得bytesを固定SHA-256へ再照合し、改変、不正JSON、HTTP失敗をHuman decisionや0件の成功へ変換しない。
- Human Decision操作はPortalに実装せず、Portal、localStorage、Telemetry、外部ServiceへReviewer、Reason、時刻を送信・保存しない。将来、Core共通API/Schemaで採用されたDecision Ledgerだけを公開Read Modelとして取込む。
- 外部一次資料Linkは新しいTabで開き、openerを分離する。stale digestはholdとして表示し、再Lock前のDecision保存を許可しない。
- Evidence Dependency Graphのcommandとruntime identityは表示対象であり実行しない。PortalはGraph、Gate結果、digest、Subject状態を書き換えず、Core Gate `pass`以外をcurrentへ昇格しない。
- Publication Gateは秘密・秘密鍵・内部URL・外部script・未知の権利を拒否する。

ネットワーク失敗、未対応Schema、署名不正、Digest不一致では新規Indexへ切り替えず、last-known-goodを維持する。障害を0件の成功に置き換えない。
