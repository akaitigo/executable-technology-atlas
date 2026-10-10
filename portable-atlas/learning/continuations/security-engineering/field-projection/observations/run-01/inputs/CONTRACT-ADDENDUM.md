# Atlas｜実装前の追補：将来増える項目

初期の [契約](CONTRACT.md) と [期待表](expected.json) の39条件を保持し、実装前の独立レビューにより1条件を追加する。`red-report` のstoreだけに `future_internal="架空の将来追加項目"` を加え、viewerのfields省略要求を比較する。

object_only は全7項目を返す。projected は元の3項目 `id,title,status` だけを返す。storeに項目が増えたことを開示許可の追加とは扱わない。これは固定1変更の確認であり、任意のschema変更を保証しない。

有効な有限集合は計40条件。projected は15許可・25拒否、object_only は23許可・17拒否となる。初期39条件の記録を後から書き換えない。不明roleの401はこの関数のcontext拒否規約で、認証処理の実装を意味しない。
