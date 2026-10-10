# 元coverageからの増分

元agentic-systemsのnext typed-bindingへ、固定著者DAG内のread-result field参照を追加した。int literalとtyped reference、unknown/cycle全plan preflight、missing/string/bool binding拒否、proposal data保持とbad coercion/promotionを実traceで比較。strict6条件は正常1・期待拒否5、bad比較2は別枠。

readは固定in-memory fixtureで外部readではない。元単元の原票は変更せず、実LLM・全攻撃防御・外部tool・権限・agent評価は未実施。未教材と次の具体3実験はREADME参照。
