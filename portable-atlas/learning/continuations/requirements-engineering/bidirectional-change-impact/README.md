# 要求変更とtest逆追跡: link欠落を「影響なし」にしない

[元Subjectの次実験2](../../../subjects/requirements-engineering/README.md#subject全体では未教材)から、要求・設計・testの固定2枝へ進む追加単元。Mac Python標準ライブラリだけでgraphを実探索する。前提はID、集合、有向edge、要求とtestの違い。

読む順番: 元Subject→[事前契約](EXPECTATIONS.md)→[UI](index.html)の2予想→容量要求変更とtestからの逆追跡→正常/逆link欠落/拒否/実Error→[手書き集合](oracle.json)と[別行列oracle](oracle.py)→[NASA原典locator](SOURCES.md)→答え/実務判断。

[既存の要求と実test/coverage教材](../../../subjects/requirements-engineering/README.md)は現在revisionと実queue proofを照合する。本単元の到達集合はtest実行やPASSを意味しない。[既存の依存graphとtest選択教材](../../../subjects/software-engineering-foundations/README.md)では「利用側→依存先」を逆方向に探索する。本単元は要求→設計→testをforward、独立保存したtest→設計→要求をreverseと呼ぶ。矢印の意味を混同しない。

## 独自保持契約と対照

容量枝R-CAP→D-CAP→T-CAPとFIFO枝R-FIFO→D-FIFO→T-FIFO。各1要求/設計/test。容量3→2という要求変更を想定し、容量枝だけの到達を測る。graphだけを計算しqueueを変更しない。到達集合は起点自身を含む。forward/reverseを独立保存し、reverseを自動再生成しない。

| 問い | 正常 | 逆D-CAP→R-CAPだけ欠落 |
|---|---|---|
| R-CAP変更 forward | R-CAP,D-CAP,T-CAP | 同3ID / TRACE_INCOMPLETE |
| T-CAPからreverse | T-CAP,D-CAP,R-CAP | T-CAP,D-CAP / TRACE_INCOMPLETE |
| 正常FIFO枝 | FIFOの3IDだけ | 容量枝へ外挿しない |

逆linkが欠けると上流要求が見えなくても、影響なしとは言えない。対応表の欠落は探索結果と別検査し、不完全を明示する。型・ID・field・edge違反はINPUT_REFUSED、実RuntimeError注入はEXECUTION_FAILUREで正常答えを隠す。存在する空forwardは不正型とは違い、起点のみ到達/trace不完全。有限入力の全優先順位は契約参照。

## 実装・再現・証拠

```sh
python3 -B runner.py --case cap-change
python3 -B runner.py --case missing-back-reverse
python3 -B checker.py
python3 -B server.py
python3 -B route.py impact
python3 -B route.py approval       # unsupported exit2
python3 -B runner.py --record     # 新receiptだけ明示保存
python3 -B checker.py --record-binding
```

serverはdynamic127.0.0.1 URLを表示。UIはPOSTで同じPython [producer](producer.py)を呼び、JSにgraph探索を複製しない。終了は自身のterminalのCtrl-Cと所有tabを閉じる。

通常runner/checker/routeは証拠を生成しない。[runner](runner.py)の明示recordは全18ケースをUTC/UUID付き新rawへ保存し、fixture/sourceSHAと実DFS traceを保持する。旧rawを上書きせず、想定外実行失敗をcurrentへ昇格しない。失敗観測も保存する。digestは改変検出で、署名や要求妥当性の証明ではない。

[oracle](oracle.py)はproducerをimportしない。実装前の手書き到達集合・逆link対応表、別Boolean隣接行列閉包を同時照合する。容量/FIFOそれぞれのforward/reverseと欠落の非対称を検算し、DFSの訪問/neighborも実入力に照合する。独立は別実装であり、別の人による要求レビューではない。

UIの条件resetは2予想・旧raw/比較/答えを初期化する。各予想欄の単独変更は新値と他欄を保持し旧raw/比較/答えを消す。起点上書きも旧結果を消す。拒否時も予想を保持して比較でき、実行失敗は正常答えへ進まない。

答え: forwardで変更先が見えることと、testから根拠要求へ戻れることは別。逆linkの欠落を「影響なし」と解釈せず、保存関係の不完全として修復/レビューする。容量枝だけという結果も固定graph内の判断である。

実務判断: 関係表とbaselineを更新し、影響testを選んだ後に実再テストを行う。結果がPASSでも要求の妥当性や変更承認を別に確かめる。未記載の結合・外部要因までこの閉包が発見するとは判断しない。

## 次の3実験（未実施）と限界

1. 共有設計/多対多で両枝へ波及する新契約を比較。NASA §3.4–3.5の多対多へ接続。
2. linkと要求revisionのbaselineを変更し、古い到達/実proofを別々に失効。[既存coverage](../../../subjects/requirements-engineering/README.md)
3. graph選択したtestを実再実行し、変更審査と人の承認未確認を別表示。[既存test選択](../../../subjects/software-engineering-foundations/README.md)

有限coverageは6node/2枝/18caseだけ。実stakeholder承認、要求の妥当性、一般的な精密変更影響、実test実行、製品graph自動解析、多対多/循環/全validation/性能は未実証。Core/fullGate/Portal/他教材/設定/install/課金/commit/push/公開は変更しない。

[fixture](fixture.json) · [current raw](evidence/current.json) · [binding](evidence/binding.json) · [実IAB QA](evidence/ui-qa.json) · [検証](evidence/verification.json) · [限定Skill](skills/atlas-bidirectional-impact/SKILL.md)
