---
name: atlas-lazy-failure
description: Atlas の固定 Kotlin/JVM 保存結果から、lazy の例外後再試行と深さ2までの再入を読み分ける。
---

# Atlas の限定案内

対象は main thread の6条件だけ。例外再試行の公開規則と、再入の固定実装観測を分ける。一般property/class委譲、並行例外、他platform、無制限再帰の問いをこの6条件で確認済みと答えない。

## Atlas の通常手順：保存結果を読む

1. このSkillから `../../status.json` と `../../reader-data.json` を読む。observationがnullなら実測なし。契約・手計算・原典・コードの読解で止め、存在しない実行ログや画像を案内しない。
2. statusで画面確認と受入の範囲を読む。`browser_start_hold` がtrueなら新しいブラウザー/サーバーを開始しない。既に利用できる画面では `../../README.md` の読む順へ進み、それ以外は保存JSON・原典・コードを案内する。画面はKotlinを実行せず、保存画像の確認と一般Agent評価は別である。
3. 例外か再入かを選ぶ。例外ではcalls0→1→2→2、初期化状態、同一参照を別々に追う。資料取得失敗を initializer 例外と扱わない。
4. 再入では inner getter / outer created / outer initializer return / outer getter / later getter を分ける。Token番号は呼出し順で、生成順は2→1。内部cacheを直接見たと説明しない。
5. 原典の公開規則と固定格納位置へ戻り、答え合わせと限界を述べる。深さ2で停止する今回の入力から一般の再入安全性を推論しない。

保存済みrunを検査するときは `python3 verify.py --run <reader-data.json の observation.path> --mutations`。ファイルへの相対位置は教材root基準。コンパイラーを起動せず、完全出力・入力hash・固定期待との一致を確認する。

## Atlas の別手順：新しく実測する

通常の案内には不要。共有担当の専有枠と許可があるときだけ、固定cache/read-only sourceの一致、fresh資源、priorityの実値を確認する。`python3 resources.py` の保存記録が allowed であれば `python3 run.py --execute --resource-record <そのpath>`。rootの共有枠なし、値が不明、gate不成立なら起動せず記録する。自動retry・期待書換え・SDK導入・他process設定変更は禁止。

このSkill文書の配置と一般的なAgent評価は別。別担当の有限な保存資料読取が実施された場合だけ、その範囲を状態記録へ示す。
