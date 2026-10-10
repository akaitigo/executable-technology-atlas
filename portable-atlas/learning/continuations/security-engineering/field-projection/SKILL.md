# Atlas｜object認可とfield開示を分けて案内する

このローカルSkillは [学習画面](index.html) と保存した合成要求の説明に限定します。自動インストールや一般Agent評価ではありません。[起動手順](REPRODUCE.md)、[初期条件](CONTRACT.md)、[追補](CONTRACT-ADDENDUM.md)、[保存結果](observations/run-01/results.json)、[原典](SOURCES.md)、[範囲](COVERAGE.md) を順に辿れます。

1. 信頼済み上流contextと利用者requestを分けて読みます。認証は仮定であると伝えます。
2. viewer / red-report の修正版を予想し、全項目の対照と3項目の応答を比べます。
3. viewer / internal_note と mixed-forbidden を開き、object許可後もfieldを拒否し、部分payloadも返さないことを読みます。
4. operatorのcontact_emailとauditorのinternal_noteを比較し、役割名だけで上下関係を推測しないと確認します。
5. future-fieldを開き、storeに項目が増えても明示許可が増えないことを説明してもらいます。
6. [原典と実装の対応](SOURCES.md)を読み、答え合わせと実務上の未確認事項を分けます。

有限な利用確認は次の3問です。

- 「objectを読めるviewerは内部メモも読める？」→いいえ。[保存結果](observations/run-01/results.json) の `viewer/field/internal_note` は修正版403/null。対照は全項目を返します。[許可表](fixture.json)のviewerを確認します。
- 「requestへrole=auditorを足せば切り替わる？」→`role-override` は400/null。contextは不変です。ただしこれを本人確認やJWT検証の実装とは呼びません。[契約の仮定](CONTRACT.md)へ戻ります。
- 「writeを拒否したからmass assignmentや本番APIも安全？」→今回の証拠では判断できません。`write-operation` は未対応操作の拒否であり、書込側field制御は [範囲外](COVERAGE.md) です。

欠落や内容不一致では古い成功結果を使わず、保存記録を確認して予想から再開します。未知の実製品や資格情報を求める利用へ広げません。本人確認・分散強制・実HTTP/DBの要求には不足を明示します。

関数比較と独立照合に加え、保存結果を読む画面の14項目・40条件の実DOM・実画像9枚を確認しました。[操作記録](qa/run-2026-10-06T143811732Z/report.json)、[作者目視](qa/self-visual-review.json)、[別担当の受入状態](qa/reader-acceptance.json)を分けて参照してください。上記3問を資料から辿る確認は、未知の質問に対する一般Agent能力の評価ではありません。
