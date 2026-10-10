---
name: atlas-udp-message-boundaries
description: Mac loopbackの保存UDP原票でdatagram境界、空payloadとEOF、recv幅不足を学び検算する教材限定Skill。WAN保証・本番操作・DNS設定には使わない。
---

# UDP message境界の追加教材

[README](../../README.md)から予想→1 recvずつ操作→比較→原典/実装→答えを案内する。通常閲覧・[checker](../../checker.py)はread-onlyでsocketを開かない。明示再採取の依頼だけ[runner](../../runner.py) `--record`を使い、既存承認とOS reviewを維持する。[原典](../../sources.json)と[入力契約](../../contracts.json)を読む。

[route](../../route.py)の有限routeを使う：datagram境界→two-datagrams、空payloadとEOF→empty-datagram、残りを次recvで読む→small-buffer、幅ぴったりの検出→exact-fit、原票検算→checker.py、明示再採取→runner.py --record。

返却bytesとsender、timeoutを読む。TCP EOF扱い版は空後のNEXTを見落とし、stream連結版は別datagramを混ぜる。候補payloadは業務検証済みではない。幅ぴったりだけで切捨てを検知できず、sent原票がある本実験の検算と汎用受信側を区別する。

WAN配送保証、再送protocol実装、DNS設定変更、本番UDP負荷試験は未対応と答え、READMEの残る実験へ案内する。loopback到達をUDPの配送/順序保証にせず、sender端点を認証にせず、sendto成功を業務ackにしない。第1TCP単元/入口97件を保全し、他pathやGoal/Portalを変更しない。次実験を自動開始しない。
