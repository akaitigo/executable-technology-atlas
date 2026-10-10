---
name: atlas-certificate-chain-name-purpose
description: このAtlas追加単元の既存runner/checker/UIで、dummy証明書のOpenSSL offline verify、chain/SAN/EKU/固定期限とoption省略の反例を比較する。実TLSやOS trust登録には使わない。
---

rootはこのファイルから `../..`。README.mdで第1単元との関係、既存toolと未実行範囲を読む。
正常は `python3 -B run.py --case normal`。名前省略反例は既定 `python3 -B run.py`。用途は `--case wrong-eku`、CAは `--case untrusted`、期限は `--case at-start` / `--case at-end`。未対応は `--mode tls` でJSON rejected/exit2を確認。
検証は `python3 -B check.py`、画面は `python3 -B server.py` の所有loopback URL。所有serverを終了。通常checkerはread-only。明示原票更新時だけ `check.py --record`。
既存実toolのoption不足を模型へ置換しない。既存runner/checker/UIだけへroute。通常の実行で証明書を再生成しない。generate.pyは明示的なdummy再生成時だけ。新秘密、real CA、OS trust/Keychain、実TLS、CRL/OCSP、browser設定は触らない。
