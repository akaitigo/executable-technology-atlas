---
name: atlas-networking-protocols
description: TCPのsendall/recv境界とlength framingを、このローカル視覚教材・Python実装・loopback観測原票で学ぶ。再送や輻輳などのpacket実測には使わない。
---

このSkillのmodule rootはこのfolderから `../..`。利用者の問いに必要な範囲だけ読む。

- 画面と手順: [index.html](../../index.html)、[README.md](../../README.md)。予想→recv操作→正常/異常parser比較→一次資料/実装→EOFの答えへ案内する。画面操作は保存済み実観測の再生。
- 実装: [framing.py](../../framing.py) は2-byte big-endian長さの蓄積decoderと、1 recv = 1 frameと仮定する比較実装。[app.js](../../app.js) は原票の図/UI再生。
- 原票: [observation-data.js](../../observation-data.js) の `artifact_directory` が現在のrun。そこにある `observation.json` / `command.json` / `manifest.json` を参照し、runtime版・観測時刻・入力・recv幅と返却bytes・exitを明示する。固定のrecv回数をTCP保証としない。
- 検算: module rootで `PYTHONDONTWRITEBYTECODE=1 python3 test_lesson.py`。socket不要のparser/原票検査であり、新しいTCP実測ではない。
- 新しい実観測を依頼された場合だけ [record_observation.py](../../record_observation.py) をmodule rootから `PYTHONDONTWRITEBYTECODE=1 python3 record_observation.py` で実行する。[observe_tcp.py](../../observe_tcp.py) が127.0.0.1の動的port・2接続・合成13 bytesを上限付きで扱う。socket listenの正式な実行許可を適用し、拒否時は未実測と返す。旧runを保存し、結果を使って説明する。

[sources.json](../../sources.json) の公式URL・版・locatorへ戻る。今回実証したのは同一Macのstream API。packet/retransmission/congestion、DNS、UDP、L2、routing、TLS、WANなどの質問にはこの教材では未対応・未観測と伝え、支持する原票があるように振る舞わない。全Subject完成・理解度達成は未測定。global install、外部設定、別repo、Core/Graphの作業をこの入口から追加しない。
