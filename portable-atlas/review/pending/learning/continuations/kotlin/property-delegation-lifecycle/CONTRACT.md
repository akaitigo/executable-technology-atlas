# Atlas：property委譲の結び付けと読書き

この契約は実装・コンパイルより先に固定する。分野目標23の固定期待による比較と、本人の委譲・スレッド安全性の問いへ対応する。前提は変数、property、関数呼出し、参照、JVM。KR-02で読んだ一般propertyの規則を、小さい実行へ進める。

## Atlas の到達目標と読む順

予想→操作→正常と設計契約違反の比較→固定原典と実装→答え→実務判断の順で、(1)結び付けのprovideDelegateと読書きのgetValue/setValue、(2)ownerとdelegateの参照、(3)読取り回数と値の保持、(4)言語上有効なコードと用途上の要求を区別する。

対象はmain threadだけ、Holder H1/H2のmember `var label: String`。同じ初期値Aを持つSlotを使い、全条件を「構築→H1を読む→再び読む→H1へXを書く→H1を読む→H2を読む」の6時点で比較する。文字列はA/X、property名はlabel。`thisRef`のowner ID、実際に提供・使用するSlot、イベント列を保存する。

## Atlas の3対照

|条件|結び付け|宣言した用途上の要求|手で導く最後の値|
|---|---|---|---|
|direct-fresh|各Holderへ別Slotを直接渡す。provideDelegateなし|H1への代入でH2を変えない|H1=X、H2=A|
|provided-fresh|同じProviderが2回のbindで新Slotを一つずつ返す|同じ要求|H1=X、H2=A|
|provided-shared|Providerが両bindへ同じSlotを返す|同じ要求を破る対照|H1=X、H2=X|

全条件のgetValueは合計4回、setValueは1回。bindはdirectで0、providedで2。共有Slotのカウンターをowner表の2行へ表示しても、同じものを合計して8/2回にしない。返値A/A/X/AまたはA/A/X/Xと、実`===`によるSlot参照の同一性を別に記録する。ID文字列の一致だけで参照同一性を証明しない。

[expected.json](expected.json)は6時点×3条件の値・回数・返値・全イベントを固定した手書き期待。監査用snapshotはSlot内部を読む専用関数で取得し、Holder.labelを余分に読まない。ログを取るための追加getを混ぜない。

共有対照はKotlinとして有効で、コンパイル/実行ともexit0を期待する。分類はexpected-design-violation。コンパイラーの拒否、例外、実行不能、timeoutを同じ成功へ数えない。今回はoperator不足のコンパイル拒否を別に増やさず、この用途上の対照で正常と異常を比較する。

## Atlas の固定原典と前提

[SOURCES.md](SOURCES.md)と[sources.json](sources.json)にKR-02の固定Docs/Spec本文、行、版、hash、局所抜粋を示す。property-access/operators/provide-delegateの規則を使う。説明図の箱や矢印はownerと参照の説明模型で、生成field形状や実メモリー画像の証拠ではない。

一般の`by`は値の記憶、ownerごとの独立、thread-safeを追加しない。lazyの初期化と公開の保証は既受入教材へ戻り、可変payloadの更新や複合操作の安全性へ広げない。class委譲の転送とoverrideは次の別の不足として残す。

## Atlas の実行上限と失敗保存

既存Kotlin 2.4.10とOpenJDK17.0.17 cacheだけ。1回の逐次batchでcompile1/JVM1、worker0、新規対象再試行0。compilerはJVM heap256MiB/15秒、JVM実行はheap64MiB/10秒、全体45秒以内。両方でActiveProcessorCount=1を指定するが、OSによる一核心への強制制限ではない。heap上限も総RSS上限とは別である。自分の子だけにCPU時間のsoft/hard上限をcompiler12/13秒、JVM8/9秒として設定し、実値を確認してから起動する。子で優先度を設定し実nice>=10を確認してから対象をexecする。設定失敗は対象起動0。所有process groupだけを有限TERM/KILL/waitで回収し、完全出力または得られた部分出力を保存する。

rootの単独実行枠と、直前の資源読取が必要。load<6、idle>=60%、memory_pressureの空き>=40%、利用可能量推定>=2GiB、合計使用CPU=(100-idle)×CPU数<=400%（一核心100%の尺度）、既知の重い他処理なし。ps等の読取不明は0件とせず停止する。rootの既存idleブラウザーは、その時点のidentityと限定判断が明示された場合だけ個別に扱い、旧57件例外を自動継承しない。通常sandboxが同じ無害読取を阻む場合は正規の審査経路を使い、拒否は迂回しない。

計算結果、入力/source hash、環境、実priority、exit、想定対照、実行失敗、回収を分離する。旧共有repo/元教材/台帳/OS/Docker設定を変更しない。install/新サービス/公開なし。

## Atlas の受入と残す限界

実装前の独立期待との照合、独立参照の意味確認、保存値への少数改変拒否、単体readerの予想/条件/reset/取得失敗/古い応答、1280/390の実DOM・実画像、限定Skillの読取利用を別確認する。ブラウザーと配信はroot既存pageを使い、作者は起動終了しない。未実行の段階は期待を測定値として表示しない。

対象は固定3条件・2owner・main thread。任意のdelegate、class委譲、委譲operator解決全体、field最適化全体、並行mutation、他platform、性能、型体系全体の保証ではない。正式Authority分類や全Behaviorの完了、159の既受入教材の再加算は行わない。通常Skillは保存資料へ案内し、新実行は別の資源確認手順へ分ける。
