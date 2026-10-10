# 操作前の有限契約と予測

正本a=Alpha/b=Beta、選択IDはa/bのみ。URL query mode=normal/shared、id=a/b。normalの未保存draftはID別に切替後も保持し、cancelは選択IDのdraftだけ破棄してその正本表示へ戻す。saveだけ選択ID正本を書き換えてそのdraftを削除。未編集IDのsaveはNO_DRAFT拒否。textはtrim後UTF-16 code units1..40。blank/unknown IDはINPUT_REFUSEDで正本/selectionを変更しない。入力欄が不正でも保存は拒否。URLは選択を表し、draft/正本を永続保存しない。

故障版は単一sharedDraftを全IDで使う。同じ操作列「a編集→b選択→b取消→実Browser戻る→a保存」では、normalはa draftを保持してaだけ保存。故障版はbにa draftを表示し、b cancelが共有draftを消すためa編集が失われa saveはNO_DRAFT。別列「a編集→b選択→b保存」ではnormalはNO_DRAFT、故障版はaのdraftをb正本へ誤保存。完全なID別状態を[手書き表](oracle.json)へ先に固定。

実Browser backは各実験の新しい所有tabでa→bの1entryだけ戻る。条件変更/初期化は新generationを作り、その前のhistory entryはSTALE_HISTORY拒否しcurrent URLを戻す。製品router/undoを実証しない。

条件変更は正本/draft/selectionと2予想欄を初期化。正本予想だけ/表示予想だけの変更では新予想と他欄を保持し、旧比較/答えを消す。state操作後も旧比較/答えは消す。入力拒否は予想対照を表示できる。明示error注入は実Errorをthrow/catchしてEXECUTION_FAILUREを表示し、正常答えを出さず、初期化まで失敗を保持する。原票は実DOM/URL/inputとproducer logを両方採取し、独立oracleへ照合する。
