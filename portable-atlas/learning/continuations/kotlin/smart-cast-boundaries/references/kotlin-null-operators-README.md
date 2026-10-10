# Kotlin：同じString?に、どの演算子を使うか

nullを許す引数にnullと文字列Adaを渡し、safe call・Elvis・非null表明・smart castを比べます。[学習画面](index.html)は保存した実行結果を読む画面です。画面操作からコンパイラを起動することはありません。

## 到達目標

1. String?の直接アクセスが、実行前に拒否される理由を説明する。
2. safe callのnull伝播を、数値0や例外と区別する。
3. Elvisがnullのときだけ右辺を評価することを観測する。
4. 非null表明のcompile成功と、null入力時のNPEを分ける。
5. 安定した引数のnull検査後にsmart castでアクセスできる理由を説明する。
6. 保存観測を再現し、未検証の入力・型・実行環境を挙げる。

## 1. 予想する

関数の引数を <code>name: String?</code> に揃えます。入力がnullかAdaかを選び、次のコードが「拒否・null・既定値・3・NPE・アクセス省略」のどれになるか、その理由を先に書いてください。

| 操作 | 比較するコード |
|---|---|
| 直接アクセス | <code>name.length</code> |
| safe call | <code>name?.length</code> |
| Elvis | <code>name?.length ?: defaultLength()</code> |
| 非null表明 | <code>name!!.length</code> |
| smart cast | <code>if (name != null) name.length</code> |

## 2. 操作する

学習画面で入力と操作を選び、予想を書いて「保存した観測を見る」を押します。入力・操作・予想を変えると以前の答えを閉じます。直接アクセスはコンパイル時の共通の拒否結果を表示します。入力を切り替えても、存在しない実行結果を生成しません。

自分で再現するときは、このフォルダー内から既存の固定ツールを指定します。

~~~sh
python3 -B run.py \
  --compiler /既存キャッシュ/kotlinc/bin/kotlinc \
  --archive /既存キャッシュ/kotlin-compiler-2.4.10.zip \
  --java /既存OpenJDK17/bin/java
python3 -B verify.py observations/表示された実行ID/run.json
~~~

パスは説明用です。既存Kotlin repoのキャッシュとこのMacのOpenJDK 17.0.17を再利用します。run.pyは配布物の固定digestと展開treeを照合し、Kotlin 2.4.10とJDK 17.0.17以外では停止します。新しいrunフォルダーにだけ結果と小さなJARを保存します。SDK変更・インストール・Gradle・Docker・ネットワークは使いません。コンパイラは最大256 MiB、使用processor数2で逐次実行します。他の実験と重ならない枠で実行してください。

## 3. 正常・拒否・実行時失敗を比べる

事前の[固定期待値](expected.json)は次の通りです。2026年10月6日11:56:03〜09 JSTのMac実測は全てこの期待値と一致しました。[実測原票](observations/20261006T025603197924Z/run.json)と[独立検証結果](observations/20261006T025603197924Z/verification.json)を保存しています。2回のcompileと8回のJVM実行を1つの逐次batchで行い、各コマンドの再試行は0回。53項目の検証と3つの誤分類反例の拒否を確認しました。

| 操作 | null入力 | Ada入力 | 起きる段階 |
|---|---|---|---|
| 直接アクセス | UNSAFE_CALLで拒否 | 同じnullable引数の宣言箇所で拒否 | コンパイル。JARなし・実行なし |
| safe call | null | 3 | 正常終了。式の型はInt? |
| Elvis | DEFAULT_EVALUATEDの後に-1 | 3。右辺の評価ログなし | 正常終了。代替値を選ぶ |
| 非null表明 | NullPointerException | 3 | コンパイルは成功、nullのときJVMが異常終了 |
| smart cast | guardのnull分岐へ進み、アクセス省略 | non-null分岐で3 | 正常終了。安定した引数を検査 |

直接アクセスのソースでは、同じ関数をnullとAdaの両方で呼ぼうとします。しかし引数型String?への未検査アクセスが拒否されるため、どちらの呼出しも実行されません。コンパイル拒否をnull入力時のNPEに読み替えないでください。

期待どおりのNPEでも、プログラムの正常終了には数えません。正常終了7件、期待した実行時失敗1件、コンパイル拒否1件を別に扱います。

## 4. 原典と実装を読む

原典は既存Kotlin Atlasのsources.lock.yamlにある公式文書commit <code>135c79983f678c6367c5cc19eb5d8445eb3c95ce</code> に固定しています。

- [公式Null safetyの固定版](https://github.com/JetBrains/kotlin-web-site/blob/135c79983f678c6367c5cc19eb5d8445eb3c95ce/docs/topics/null-safety.md)：nullableへの直接アクセス、Safe call、Elvis、Not-null assertionの各節。
- [公式Type checks and castsの固定版](https://github.com/JetBrains/kotlin-web-site/blob/135c79983f678c6367c5cc19eb5d8445eb3c95ce/docs/topics/typecasts.md)：Smart castsとSmart cast prerequisites。
- [4操作の実装](src/NullableOperators.kt)／[直接アクセスの拒否例](src/UnsafeCall.kt)／[収集器](run.py)／[独立検証器](verify.py)／[固定原典一覧](sources.json)。

検証器はKotlinを再実行しません。実装をインポートせず、実行前に作成した期待stdout・exit・diagnostic・JAR有無を保存観測と比較します。nullを0へ読み替える、NPEを正常終了にする、compile拒否を実行済みにする、という3つの反例もメモリ上で拒否確認します。

## 5. 答え合わせする

safe callは今回、受け手がnullならnullを返しました。Elvisではそのnullを既定値-1へ置き換え、右辺の関数が呼ばれた印も出ました。Adaでは長さ3がそのまま使われ、右辺は呼ばれませんでした。

非null表明は「nullではないと確認できた」という証拠を増やす操作ではありません。今回のnull入力はcompileできてもNPEになりました。smart castの例は関数引数が途中で変わらないため、nullでない分岐の中でlengthへアクセスできます。

![コンパイル拒否と実行結果を分ける模式図](null-flow.svg)

## 6. 限界と次の課題

今回の入力はnullとASCIIのAdaだけ、実行環境は固定Kotlin/JVMとOpenJDK 17のMacです。空文字列、Unicode文字数、変更可能なproperty・独自getter・並行書換えによるsmart castの制約、Java platform type、nullability annotation、generic、Native・JS・Wasm・Androidはこの実験では検証しません。

既存のnullability-diagnosticsはJava platform typeと非null型へのnull代入を扱います。今回の成果へ重複加算しません。既存Labにもguardやsmart castの利用例がありますが、この同一String?への4操作比較とは学習目的を分けています。[COVERAGE](COVERAGE.md)に未教材範囲の根拠と残課題を記録しました。

既存ChromiumをPlaywrightの実ポインターで操作し、5操作×2入力の表示原票一致、予想変更時のリセット、幅1280／390の表示など15項目を確認しました。[ブラウザ原票](browser-qa/2026-10-06T025702128Z/report.json)、[幅1280の実画面](browser-qa/2026-10-06T025702128Z/desktop-full.png)、[幅390の実画面](browser-qa/2026-10-06T025702128Z/mobile-full.png)、[4画像の目視記録](browser-qa/visual-review.json)を保存しています。自分のbrowser contextと一時profileは終了・削除済みです。

最初のブラウザ起動は実行環境sandbox内でmacOSの初期化に失敗し、0項目・0画像の[失敗原票](browser-qa/2026-10-06T025637245Z/report.json)を保存しました。その後、このローカル検証コマンドだけの環境sandbox外実行が承認され、Chromium自身のsandboxを有効にしたまま成功しました。コンパイラ実験の再試行とは分けて記録しています。

[検証状態](observations/status.json)から各原票をたどれます。図は模式図であり、実画面画像やコンパイラ内部の図ではありません。Atlasの受入・検索・統合は未完了です。
