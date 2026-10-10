# 有限範囲／全Subjectの未教材Coverage

独自JSON ASTのInt/Var/Let/Fn/Call/Add、単parameter closure、immutable frame extension、lexical scope、call-by-valueの有限評価だけを実装しました。FnはEnvironment参照を保持し、Let initializerは外側で評価、Callはfn→有効Closureならarg→body、Addはleft→right→整数guardです。not-callableはarg評価前に止める独自順序。Schemeの評価順や全仕様の再実装ではありません。

ASTはexact field、64node/depth16、literal -1000..1000（bool不可）、name `[a-z][a-z0-9_]{0,15}`。Add結果はliteral範囲へ丸めません。evaluationは64 node enterまでで停止。resource guardはtermination証明でも強固なsandbox保証でもありません。JSON treeだけで、text parser・任意Python code・循環object・外部I/O・mutationを受け付けるAPIではありません。

保存13caseはcapture10/20、parameter7/7、arg30/40、escaped10/20、initializer11、unbound/caller rescue、not-callable/addition-type、正常0、AST拒否2、self-application budget停止。step traceのframe/closure IDはrun内の識別子。previewsのdiagramを実機memory/addressや完全なRuntime lifetime分析へ流用しません。

未教材／未実証:

- syntax/binding foundations：text parser、formal grammar、free variable analysis、alpha equivalence、capture-avoiding substitution、de Bruijn、binding resolution/compiler transform、hygienic macro、letrec/recursive definition。
- semantics：formal big/small-step導出、evaluation contexts、determinism/confluence、normalization/termination証明、denotational/axiomatic semantics、observational/contextual equivalence、bisimulation/full abstraction、logical relations。
- types：static typing/inference、progress/preservation、type soundness、polymorphism/parametricity、subtyping、recursive/existential/dependent/refinement types、linear/ownership/effect types。Runtime guardは一般型体系ではありません。
- values/effects/control：boolean/product/sum/list/recursive data、pattern matching、mutable store/location、aliasing、exceptions、continuations、algebraic effects、evaluation strategy比較、recursion/TCO。
- composition/runtime：module/signature、ADT、class/object/prototype、closure conversion、GC/lifetime、region/ownership、FFI、compiler/runtime implementationと互換性。
- concurrency/security：thread/actor/channel、interleaving、atomic/memory consistency、data race、deadlock/fairness、capability、noninterference、side-channel、形式的安全性と実Runtime事故/回復。

README/indexの次4実験はbinding/substitution、small-step、Int/arrow typing、mutable storeへの学習経路で、未実施です。それらでも上記全範囲は閉じません。今回の有限200例・hand chain・改変検査を全入力網羅や証明、実言語のconcurrency/type/runtimeのEvidenceへ昇格しません。
