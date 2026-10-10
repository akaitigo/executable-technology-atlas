---
name: atlas-body-size-budget
description: 固定plain/gzip bodyを実loopback HTTPとBrowser ResourceTimingで比較し、encoded budgetへのdecoded値流用を検査する有限教材。
---

# bodyサイズを比較する

../../README.md と ../../EXPECTATIONS.md を先に読む。body-budgetは ../../producer.py、compareは ../../index.html、verifyは ../../checker.py、sourcesは ../../SOURCES.md へ ../../route.py でroute。自分のserverが印字する動的portのみlive runnerへ渡す。

通常checker/routeはread-only。保存要求だけ明示 --record。独立literal hex、http.client生response/decompress、Browser実ResourceTimingを区別し、header値をBrowser測定へ代入しない。timing欠測/0/不整合は成功にしない。全入力変更で旧本文空・閉鎖・新値保持。

wire-total、latency、cache-cdn、web-vitals、cross-originはunsupported。body budgetを全performanceや実wire総bytesの実証と扱わない。追加installや元Subject/Portal/Core/fullGateの変更は行わない。
