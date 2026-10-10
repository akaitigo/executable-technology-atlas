# 浮動小数点総和の丸めと補償

Catalog ID: `computational-mathematics-numerical`。小さい入力を自分で変え、総和の順序・丸め・桁落ちを観察する独立教材です。Mac標準CPythonとstdlibだけで計算し、背景IABで実画面を確認しました。

## 予想 → 操作

`[1e16, 1, -1e16]`の数学的な総和は1です。実行する前に、naive、基本Kahan、Neumaierで同じ結果になるか予想してください。次に`[1e16, 1, 1, -1e16]`へ1を追加し、入力順と絶対値の小さい順を比べます。「小さい順なら常に正確」という予想も3項の例で確認してください。

このdirectoryで起動します。package installやbuildはありません。

```bash
/usr/bin/python3 -B lesson.py --port 18746
```

ブラウザで`http://127.0.0.1:18746`を開きます。比較例、順序、十進数入力、予想を設定して「Pythonで計算して比較」を押してください。結果を見た後、step sliderを動かし、どの入力で値や補償値が変わったか確認します。途中のstepを動かしても上のカードは全入力の最終結果、下の表は選択prefixの結果です。

入力は1〜32個の十進数文字列、各40文字以内。明示する十進指数は-100〜100、非ゼロ値は変換後floatで概ね`1e-100`〜`1e100`の範囲です。NaN、Infinity、範囲外、underflow、空入力を拒否します。`NaN`を入力して拒否を観察した後、正常例へ戻して回復を確かめられます。サーバーはloopback限定です。終了は起動したターミナルで`Ctrl-C`。

## 正常 / 境界の実測

2026-10-05 13:32 JSTのCLI観測。CPython 3.9.6、macOS arm64、float radix 2、mantissa 53 bit、rounds 1。最終時刻と環境は[Python原票](observations/python.json)が正本です。

| 入力 / 順序 | naive | 基本Kahan | Neumaier | math.fsum | 十進数Fraction oracle |
|---|---:|---:|---:|---:|---:|
| 1, 2, 3, 4 | 10 | 10 | 10 | 10 | 10 |
| 1e16, 1, -1e16 | 0 | 0 | 1 | 1 | 1 |
| 1e16, 1, 1, -1e16 | 0 | 2 | 2 | 2 | 2 |
| 同じ4項、絶対値の小さい順 | 2 | 2 | 2 | 2 | 2 |
| 同じ3項、絶対値の小さい順 | 0 | 0 | 1 | 1 | 1 |
| 0.1を10回 | 0.9999999999999999 | 1 | 1 | 1 | 1 |
| 1, -1 | 0 | 0 | 0 | 0 | 0 |

![境界例の実画面](media/cancellation.jpg)

小さい1が大きな部分和へ足されると、表現可能なfloatへ丸められて消えることがあります。その後の大きな正負の相殺で、失われた1が答えに露出します。最後の減算だけを誤差の発生地点と決めつけず、step 2の結果と補償値を読んでください。

![0.1を10回の実画面](media/decimal.jpg)

`0.1`の例では入力変換誤差もあります。Neumaierの最終結果1は十進数oracleに一致しますが、変換後floatの厳密な総和に対する誤差は`-1/18014398509481984`です。「総誤差ゼロ」と「計算誤差ゼロ」は別の問いです。

## 一次資料 / 実装 → 答え

[Python公式の浮動小数点解説](https://docs.python.org/3.9/tutorial/floatingpoint.html)は入力の二進表現と表示の丸めを説明します。[Fraction公式仕様](https://docs.python.org/3.9/library/fractions.html)では十進数文字列とfloatの構築を区別できます。本教材のoracleは次の2種類です。

- `sum(Fraction(token))`: 利用者が入力した十進数の正確な総和。
- `sum(Fraction.from_float(x))`: 実際に計算へ入ったfloatの正確な総和。

誤差の正本はFraction。Decimalは70桁の表示用であり、oracleを有限精度Decimal総和で置き換えていません。相対誤差は十進数oracleが0なら定義せず、UIでもそう表示します。

[lesson.py](lesson.py)の`experiment`ではnaiveを明示的な左からの`+=`で実装しています。Pythonのbuilt-in `sum`は版ごとの実装差があるため、naiveの定義に使っていません。

基本Kahanは`y=x-c; t=s+y; c=(t-s)-y; s=t`。Neumaierは`|s|>=|x|`なら`(s-t)+x`、そうでなければ`(x-t)+s`を補償に足し、最終的に`s+c`を返します。補償の符号・用途が違うため、cの数値だけを同一視しません。[Kahan本人の資料 §3](https://people.eecs.berkeley.edu/~wkahan/Mindless.pdf)は補償計算の括弧を代数的に消す問題を説明し、[Neumaier (1974), 著者公開版](https://arnold-neumaier.at/scan/01.pdf)は総和の丸め誤差を扱います。教材のコードは小規模比較用の実装で、第三者本文を保存していません。

[math.fsum公式仕様](https://docs.python.org/3.9/library/math.html#math.fsum)と[CPython v3.9.6実装](https://github.com/python/cpython/blob/v3.9.6/Modules/mathmodule.c)も比較入口です。`fsum`はpartial sumsを保持するstdlibの実装で、この教材のNeumaierと同じアルゴリズムではありません。公式仕様には環境によるdouble roundingの注意があります。参照した3.9系文書の表示版は3.9.25、実行したMac標準Pythonは3.9.6です。全環境での正しく丸められた答えや誤差上限を本実験から保証しません。

答え: 加算順序と補償方法は結果を変え得ます。Neumaierがこの境界例を回復したこと、Kahanが4項の例を回復したことを実測できました。sortや補償を万能な修正にせず、入力の数学的な意味と実行floatの両方へ結果を照合します。

## 再現と検証記録

```bash
# 保存済み結果と現在sourceを照合し、9件のテストを実行
/usr/bin/python3 -B verify.py

# 新しいCLI観測へ更新（既存python.json/stdout.txtを更新する）
/usr/bin/python3 -B lesson.py --record

# 別ターミナルでserverを起動済みの場合、実HTTP原票を更新
/usr/bin/python3 -B verify.py --http
```

[stdout.txt](observations/stdout.txt)は実行時にprintしたJSON linesそのものです。[tests.txt](observations/tests.txt)はテスト実行出力、[http.json](observations/http.json)は実HTTP statusと未加工の応答bodyです。5入力×3順序、7種類の拒否入力、9件のfocused test、HTTP正常/境界/NaN/範囲外/回復を確認しました。

背景IABで例選択、順序変更、step slider、NaNと範囲外の拒否、正常への回復を操作しました。[ui-dom.json](observations/ui-dom.json)に実DOM原票と観測時刻、[media.json](observations/media.json)にJPEGの寸法・digest・source bindingを保存します。スクリーンショットは全ページ静止画で、操作動画ではありません。日本語、数値、誤差plot、入力、正常/拒否/回復の可読性を目視確認しました。ブラウザengineの版は今回の観測APIでは取得していません。スマートフォン寸法の実画面QAは未実施です。

図の縦軸は各入力セットで自動調整し、最小上限を`1e-16`にしています。それより微小な計算誤差は図上で見分けにくい場合があるため、数値表とFraction表示で確認してください。JavaScriptの座標化自体の丸めも含む説明用図です。

最初の8件テストは「3項を小さい順にするとnaiveが1になる」という誤った期待値で1件失敗しました。4項の改善例と3項の非改善例を独立して検査する9件へ修正しました。最初のserver起動はsandboxのsocket bind拒否で失敗し、host permission review後に起動しました。[初期失敗記録](observations/initial-failures.txt)を保持しています。

## 説明モデルと未教材範囲

| 軸 | この教材で扱う範囲 / 制限 |
|---|---|
| 総和 | 小規模・有限・逐次・実Mac Python float、Kahan/Neumaier/fsum |
| oracle | 十進数文字列と変換後floatの正確なFraction総和 |
| 図 | Pythonの各prefix計算誤差をJavaScriptで座標化。`log1p`で微小誤差を描画 |
| Python / JS差 | JSの総和は実行していない。同じ結果・精度とは宣言しない |
| 行列・線形代数 | 未教材: 分解、固有値、疎行列、線形solver |
| ODE / PDE / FFT | 未教材: 時間積分、安定領域、空間離散化、変換誤差 |
| 条件数・誤差解析 | 正式な条件数、forward/backward errorの定理、保証は未教材 |
| 並列・GPU・大規模入力 | 未測定: reduction順序、FMA、SIMD、異なる丸めmode、性能 |
| 非有限・極端な指数 | UIで拒否。IEEE例外、overflow/underflow後の計算法は未教材 |
| 理解度 | 利用者の理解度と分野全体の完成は測定していない |

## Skill入口

[atlas-computational-mathematics-numerical](skills/atlas-computational-mathematics-numerical/SKILL.md)はこの実装・checker・画面・原票を再利用する限定入口です。global installはしていません。frontmatter/namingを`skill-creator/scripts/quick_validate.py`で検証し、正常総和、Kahan境界、未対応ODE/JS比較の依頼をlocal read/controlで確認しています。[Skill確認記録](observations/skill-review.md)に確認範囲を残しました。独立Agentや全SubjectのSkill評価ではありません。

作成・検証はこの教材directory内で完結します。既存PortalやSubjectの完成判定を変更せず、公開・commit・pushは行っていません。
