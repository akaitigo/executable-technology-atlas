# 原典locator・確認状態・独自導出

- [MIT 18.086 Spring 2006, 8 Feb transcript](https://ocw.mit.edu/courses/18-086-mathematical-methods-for-engineers-ii-spring-2006/806b14f6a7a07a2209735c5162b567aa_gv-AB35V2k8.pdf): 今回本文取得。PDF pp.9–10のforward Eulerの増幅係数と負実固有値の境界、pp.10–11のbackward Eulerの係数・安定性を確認。本教材のplant係数−3へ適用した式は作者の導出。
- [SciPy cont2discrete](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.cont2discrete.html): method欄のeuler/backward_diff/zoh、Notesの離散化手法区別を本文確認。参考locatorとして読み、SciPyをinstall/実行したとはしない。plantのZOH離散化と連続閉ループを閉じてからの離散化の違いは[独自導出](DERIVATION.md)で示す。
- [Python 3.9 decimal](https://docs.python.org/3.9/library/decimal.html): precision/contextとexp/lnのAPIを本文確認。表示docs版3.9.25、実行CPythonはrawの環境欄。precision80の[oracle](oracle.py)はclosed formを評価し、float反復を呼ばない。

取得attempt: 2026-10-05、上記3資料成功。MIT 16.90 Chapter6 locator `https://web.mit.edu/16.90/BackUp/www/pdfs/Chapter6.pdf` はtoolでアクセス不能。この取得失敗を保持し、根拠に使わない。第1単元の資料取得状態は変更しない。第三者本文・図は保存しない。

独自model契約: tau1/K2/r1/y0=0/clipなし/T8、h=.1/.2/.8/1.6。[fixture](fixture.json)と[DERIVATION](DERIVATION.md)を実run前に固定。数学CPU計算で、実plant・HIL・PID全体・安全性を実証していない。
