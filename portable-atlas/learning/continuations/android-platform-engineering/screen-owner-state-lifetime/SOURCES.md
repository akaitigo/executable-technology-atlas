# 公式根拠とPython模型の境界

[Android ViewModel overview](https://developer.android.com/topic/libraries/architecture/viewmodel) の「Scope」「The lifecycle of a ViewModel」を制作時に取得確認。ViewModelはViewModelStoreOwnerのscopeに結びつき、configuration changeを越えて保持され、activity finishやnavigation entryの除去等のowner終了で寿命が終わると説明される。本教材はそのownerとviewの寿命差を明示Python表へ対応させる。API実行ではない。

[Save UI states (Views)](https://developer.android.com/topic/libraries/architecture/views/saving-states-views) のViewModelとsaved instance stateの比較を取得確認。memory上のstate holderとprocess deathを越える保存手段は区別される。本単元はin-memoryだけでsaved tokenや復元を実装しない。保存が必ず最新・利用可能という保証を導かない。

独自のp1:B:2というidentity、view generation、初期A2/B1、最大8event、restart opは教材契約。[固定表](oracle.json)・[事前契約](EXPECTATIONS.md)・[producer](producer.py)へ戻る。実Android callback順・Compose・SavedStateHandle・実process再開の検証ではない。

[元Activity/process教材](../../../subjects/android-platform-engineering/README.md)→[元COVERAGE次1](../../../subjects/android-platform-engineering/COVERAGE.md)→本単元→[version付き保存codec](../../apple-platforms-engineering/versioned-codable-presence/README.md)の順。codecは別platformの独自JSON schemaで、Android保存APIや本ownerの永続性を実装したものではない。既存教材をruntimeで呼び出さない。
