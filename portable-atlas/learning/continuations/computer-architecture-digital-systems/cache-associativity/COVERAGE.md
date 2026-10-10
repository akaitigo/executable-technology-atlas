# Atlas：既存direct-readから配置の選択へ

目標09（`2026-10-06/task-8/atlas-97-field-goals-ja.md:139–149`）の「小モデルのアドレス状態を追い、同条件で設計比較する」ための続編です。元分野README:3/9–24はread-only direct-mappedの配置・byte・故障tag比較、COVERAGE:11はset associative/LRUを未対応としています。

最新180受入と学習経路を照合し、旧write-policy-dirty-evictionは容量4B/line4B/1行の書戻し、RV32I pipelineは命令のRAWを対象としていることを確認しました。今回の5trace×正常2方式＋LRU更新省略1対照は、同16B/line4Bでset/way/victim/recencyを比較する不足へ限定します。一般cache/商余り/取得byteの基礎、前作の0/16競合、write policyを新しい成果として再加算しません。

前提は二進数・商/余り、byteとblock、valid/tag、cold start、元direct-read教材です。同容量でwaysを増やすとset数も減ることを確認し、2-wayが必ず有利だという誤解と、hit後のLRU更新省略を区別します。実CPU性能、write/dirty、多段/coherence、任意入力や全traceの定理は対象外です。

共有元のowner取得不能/Portal配置形式の制約は既存の継続記録として保持し、共有repo/180成果/集計は変更しません。現在状態はstatus.jsonを正とし、未実行の手表を実測とは呼びません。元path/読取箇所/hashはrecords/reuse-and-scope.jsonへ。
