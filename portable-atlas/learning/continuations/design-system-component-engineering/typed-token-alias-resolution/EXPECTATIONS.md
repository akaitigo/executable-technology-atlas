# 実装前の固定color subset契約

5固定token: primitive.blue/green、semantic.action/focus/positive。通常action→blue、focus→action、positive→green。blue値をredに変更するとaction/focusのA/B背景とfocus outlineがred、positive badgeはgreen。action参照をgreenへ変更するとA/B/focusもgreen。

tokenは明示$type/$valueのみ、groupはprimitive/semantic固定。colorSpace=srgb、componentsはboolを除く有限number3個・0..1。alphaは省略時1、指定時1だけ。このsubsetはhex/none/他空間/半透明/継承type/$ref/JSON Pointer/metadata/複合型を未対応として拒否する。DTCG全spec適合を主張しない。numberはaliasの型不一致を検査するため認識するだけでCSS変換未対応。

aliasは値全体が `{group.token}`、参照先が既知、宣言type一致、cycle無しを全tokenで検査してからCSSを生成する。拒否時css/resolvedはnull、旧CSSを残さない。優先: group/token構造→literal/alias構文→参照探索・type/cycle→全color確認→CSS生成。missing/cycle/type mismatchをfallbackの色で隠さない。

CSSは#token-scopeへの5custom property。不透明sRGBの3components×255をfloor(x+0.5)で8bit化し `rgb(r g b)`。0.5→128は独自変換方針で、DTCGがこの丸めを強制するとは呼ばない。

故障版は正しいtoken入力を検証・解決した後、alias CSSだけ `var(--unresolved-...)` を誤生成。未定義参照でA/B/positive背景は透明、focus outlineはcurrentColorのrgb(20,30,40)を実Browserで期待。CSS生成成功と実computed一致は別。正常=blue背景/outline、故障=透明/暗色。故障観測を正常設計の成功と呼ばない。

[手計算oracle](oracle.json)はproducer実行前に固定する。全caseの最終参照先、sRGB、期待CSS全文、Browser computed値を保存。resolverはoracleに共有しない。実DOMからsampleのgetComputedStyleとscopeのcustom propertyを別readして照合する。

実Error注入はEXECUTION_FAILURE、CSS/解決結果なし、答え本文空・details閉じる。構造拒否はINPUT_REFUSEDで予想と理由を比較できる。正常/故障/拒否/失敗を別表示。

全予想controlごとに成功比較→答えdetailsを開く→その予想だけ変更を実IABで検査。新予想と他欄は保持、旧raw/CSS/computed表示/答え本文は空、detailsは閉じて隠す。条件resetは両予想・JSON上書きも消す。通常checker/runner/routeは全hash/mtime不変。明示recordは実child attempt/exit/stdoutとsourceSHAの新receipt、旧raw保持。
