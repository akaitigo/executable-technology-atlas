---
name: quadratic-cancellation
description: 二次公式と根の積を使う方式を同じfloat係数で比較し、元の十進根・丸めた係数の高精度根・実float解の3層から桁落ちと誤差を読む。
---

# 二次式の有限実験

READMEとCONTRACTを読む。Python標準libraryだけでserve.pyを起動し、自分の動的localhostを開く。既存のserver/tabを停止しない。

severeで非zero根が0になるか予測して通常公式を実行し、減算の二つの項を見る。積方式を同じfloat係数で比較する。scaled-severeでは絶対residual、term尺度、係数尺度を区別し、小さい残差だけで根を正しいと判定しない。

FNC §1.4.1へ戻り、negativeのq符号、zero根の相対誤差、double-zeroのq0特例、near-doubleとrounded-doubleの相違を説明する。元の根とfloat係数の根を同一視しない。通常公式を意図的欠陥とは呼ばない。

verify.py/route.pyは既存raw・receiptをread-onlyで照合する。実表示の確認とCLIを区別し、旧証拠を上書きしない。160/240桁照合は有限fixtureの証拠であり、任意係数の保証ではない。実験後は自分のserver/tabだけ閉じる。
