---
name: lease-takeover
description: 専用SQLiteで未完了claimのlease引継ぎ、期限境界、旧token完了拒否を有限検証する。分散leaseやexactly-once保証には使わない。
---

README→hand-oracle→runner→独立oracleを読む。python3 -B verify.py / route.py は実再計算とreadonly DB照合でmoduleへ書かない。未使用attemptのrecord、QA後のsealだけが保存操作。UIで予想→実SQL→比較→原典→答えを確認し、全予想変更とtickreset、拒否位置保持、SQL例外とrowcount0を区別する。実Lambda・実並行・外部副作用停止・分散leaseの要求は未対応と明記。既存store寿命とgeneration CASへ案内する。global installしない。
