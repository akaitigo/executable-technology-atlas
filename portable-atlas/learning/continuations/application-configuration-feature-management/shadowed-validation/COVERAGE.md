# Atlas：目標32の検証時点を比べる

目標文書 `2026-10-06/task-8/atlas-97-field-goals-ja.md:394–403` と、元subject `application-configuration-feature-management/coverage.json` の次実験 `shadowed invalid layer` を根拠とします。元READMEは各layer型検査と優先順位を説明していますが、隠れる不正の対照は次実験です。最新186の学習経路も照合し、atomic-reload-snapshotは採用後の版/読取整合性で別の問いと確認しました。

今回の増分は、同じ6合成入力の全層parseと勝者だけparseで、何を検査せず残したかを含めて比較することです。型/優先順位/rollout/更新並行性そのものは再加算しません。下位不正を常に許す/常に拒否する普遍方針はなく、運用の要件に結び付けます。

残る問いはschema migration、default更新、remote provider、fall back、複数writer/永続reload、秘密の保管/権限、実appへの適用です。全schema/全Python/OpenFeature適合・一般Agent能力・科目全体の完成は保証しません。共有owner未到達は不存在の推定へ変えず、共有元/完成186/集計はread-only、作者加算0・未統合を保持します。実施状態は[status](status.json)に分けます。
