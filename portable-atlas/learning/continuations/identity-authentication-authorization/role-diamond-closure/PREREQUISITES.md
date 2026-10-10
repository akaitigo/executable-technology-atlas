# Atlas：この実験へ進む前に

集合の和・積・重複除去、graphの有向edgeと到達、DFSの現在経路を前提にします。roleの直接grantとsubjectへのrole割当、認証と認可、actionとscopeを区別してください。

1. 元のID認証認可教材でeditor→viewerの継承、scope越境、新policyでのgrant削除を読む。
2. resource-scope-enforcementで、申告scopeと信頼resource属性の結合、deny時に読取り0となる境界を読む。
3. この教材で4role菱形を辿り、現在経路から外れた共有祖先と、現在経路へ戻るedgeを分ける。

元教材は既にvisiting/orderedを使ってcycle検出します。新しい問いは菱形全状態と権限出所の照合で、一般DFSを初めて実装した教材ではありません。



この単体教材では認証済み・scope完全一致を仮定し、実Credential/個人データ/resourceを読みません。必要な前提を上に説明し、元path/読取hashは[再利用記録](records/reuse-and-scope.json)へ分けました。[操作画面](index.html)へ戻れます。
