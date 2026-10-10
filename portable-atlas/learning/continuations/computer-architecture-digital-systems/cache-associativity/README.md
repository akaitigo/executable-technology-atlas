# Atlas：空きの数だけでは決まらない

同じ16Bのcacheでも、blockを置ける場所と捨てる順序で結果が変わります。direct-mappedと2-wayを同じline幅・cold start・read traceで比べ、hit数だけでは見えないset/way/victimと返却byteを追います。

[前提](PREREQUISITES.md) → [予想と保存結果](index.html) → [手追跡](HAND_TRACE.md) → [原典・実装](reference.html) → [Skillの6問](SKILL.md)の順に進みます。現在の実施状態は[status](status.json)を正とします。

まず`0,16,0,16`で2-wayなら残るblockを予想し、次に`0,8,16,0,8`へ変えます。「wayが増えたから必ずhitが増える」と言えるでしょうか。最後にhit-recencyの通常版と故障版を比較します。どちらもbyteが正しくても、どのblockを追い出したかは異なります。

5traceは容量16B/line4B、合成256B memoryからreadする有限模型です。directは4set×1way、2-wayは2set×2way。metadata容量・実CPU速度・write/dirtyを比較した結果ではありません。[範囲](COVERAGE.md)と[実装前契約](CONTRACT.md)へ。

## 保存画面を開く

このディレクトリをloopbackで配信する通常例です。空いているportを選んでください。



`http://127.0.0.1:8765/` を開きます。画面は保存bundleを読むもので、操作のたびに模型を実行しません。Markdown/コードは配信設定により本文表示かdownloadになるので、取得と実DOM表示を分けます。直接file URLは対象外です。

初回の模型計算は保存済みです。11結果・48readを実装前の手期待へ照合し、画面はその保存byteを読みます。rootの同じpageで59主要時点と1280/390の10viewportを確認しました。全画像が全内容を含むとは扱いません。[計算の記録](MEASUREMENTS.md)と[GUIの範囲](GUI_VERIFICATION.md)を別に残します。

## 判断へ戻る

同容量か、line幅・初期状態・入力順が同じかを最初にそろえます。hit/miss、取得byte、正しい返値、置換規則を分けて比べます。今回の2-way不利なtraceを一般的な優劣へ広げず、実装や実機の設計目的に合った追加観測が必要か判断します。

## 計算を再現する場合

保存結果の閲覧には再計算は不要です。再現時は全体負荷と他の重い処理を確認し、単独で実行できる枠を確保します。Python標準環境だけで、新しい出力名を使います。次はこのディレクトリでの例で、対象子をnice10・wall5秒で制限し、自動再試行しません。既存出力への上書きは拒否します。

```sh
python3 -B - <<'PYRUN'
import subprocess, sys
subprocess.run(["nice", "-n", "10", sys.executable, "-B", "run.py", "--output", "observations/reproduction-01.json"], timeout=5, check=True)
PYRUN
python3 -B verify.py observations/reproduction-01.json
```

この例は今回のroot管理実行をもう一度行った記録ではありません。今回の固定入力・実行記録は[計算の記録](MEASUREMENTS.md)へ。結果JSONを画面へ接続する `build_bundle.py --raw …` は保存値を検査してから同梱する手順で、現在の凍結教材を変更せず別の作業コピーで使います。
