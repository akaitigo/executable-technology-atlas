---
name: atlas-network-platform-security
description: このAtlasの合成IPv4 firewall教材でfirst matchとnaive any allow、rule順序、入力境界を既存runner/checker/UIで比較する。host firewall設定や実通信には使わない。
---

教材rootはこのファイルから `../..`。README.mdの固定権限表とcoverageを読む。
正常/迂回は `python3 -B run.py --source 10.0.0.130 --protocol tcp --port 443 --order deny-first`。順序差は `--order allow-first`。独立oracleと境界は `python3 -B check.py`。
UIは `python3 -B server.py` のloopback URLで予想→操作→flow→原典→答え。所有serverを終了する。通常checkerはread-only。原票更新は依頼がある場合の `check.py --record` に限定する。
未対応IPv6/ICMPは既存runnerの入力拒否を確認する。OS firewall、iptables、実packet filtering、TLS検証、公開を要求されたらこの教材の未教材coverageと区別し、READMEを案内する。新たなrunnerや外部設定を作らず、対象scopeを広げない。
