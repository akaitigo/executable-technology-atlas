# Atlas｜SECDED教材の一次資料

2026-10-06にMIT OpenCourseWareの公開PDFを参照しました。PDFの再配布や本文の転載は行いません。

- [MIT 6.02, Fall 2012, Chapter 6](https://ocw.mit.edu/courses/6-02-introduction-to-eecs-ii-digital-communication-systems-fall-2012/34b7d78e0b90235095ef81542f6aa2dc_MIT6_02F12_chap06.pdf)。§6.2はハミング距離による復号、§6.3はシンドロームを扱います。印刷ページ79のProblem 2は、全体を偶数パリティにする追加ビットを考える問題です。
- [MIT 6.004, Spring 2009, Tutorial 1](https://ocw.mit.edu/courses/6-004-computation-structures-spring-2009/8ef531797e54260f68c2a430932d1630_MIT6_004s09_tutor01.pdf)。最終ページのProblem 6で、2の累乗位置にパリティを置く構成と、二重誤り検出のための追加を扱います。

4分岐の日本語表と具体的な計算例は、この教材の固定配置 `p1 p2 d1 p4 d2 d3 d4 p8` から作りました。MIT 6.02のデータ・検査列の並びを、そのまま位置番号へ流用していません。原典にこの教材の1056条件やGUIの測定結果が掲載されているという意味ではありません。

最小距離・全256受信語の分布・592/464条件の結果は、この教材のコードで計算し、別方式と別担当で照合しました。一次資料の説明、独自の有限計算、画面操作の確認を区別して読みます。実通信・ハードウェアの動作を測った資料としては使用していません。
