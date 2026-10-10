# 原典と有限モデル

[MIT OCW6.450 Ch8 Detection, coding, and decoding](https://ocw.mit.edu/courses/6-450-principles-of-digital-communications-i-fall-2006/f6c75b427b022503f5c605db7de4d46f_book_8.pdf)、Robert Gallager、Fall2006。2026-10-06 JSTに56頁PDF本文を取得。§8.1（印刷249–251、PDF1–3頁）は観測に基づく選択と誤り、確率model、MAPの前提を説明。§8.2（印刷251–253、PDF3–5頁）はbinary detection、likelihood ratio、priorに依存する閾値を説明する。

今回のmagnitude/residual gateは教材の独自品質判断。likelihood、prior、確率modelを推定しておらず、MITのgate、MAP/ML detectorとは呼ばない。低residualはknown pilotへの最小二乗整合であり、payload位相の真偽を判断する十分統計量だとは主張しない。

モデルの式、正規化分母、等値、ゼロ処理はEXPECTATIONSで定め、手literalと独立成分normal equations/energy identityで照合する。受信signalは合成I/Q。正解bitsはharnessの答え合わせだけに使う。BERは比較した4payload bitsの誤り割合で、統計的BER一般へ外挿しない。既存telecom-sdr READMEは文書参照だけ、runtime依存しない。pulse-window timingは変更しない。
