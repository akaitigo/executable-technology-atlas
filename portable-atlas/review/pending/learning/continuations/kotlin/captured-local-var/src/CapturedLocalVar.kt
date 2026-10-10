// SPDX-License-Identifier: Apache-2.0
private fun display(value: String?): String = value ?: "<null>"

private fun localControl(initial: String?) {
    var local: String? = initial
    println("CONTROL_INITIAL=" + display(local))
    if (local != null) {
        println("RESULT=" + local.length)
    } else {
        println("RESULT=SKIPPED")
    }
    println("CONTROL_FINAL=" + display(local))
}

private fun capturedSnapshot(initial: String?) {
    var local: String? = initial
    val mutate: () -> Unit = {
        local = if (local == null) "Ada" else null
        println("MUTATION_APPLIED")
    }
    println("CAPTURED_INITIAL=" + display(local))
    val snapshot: String? = local
    println("SNAPSHOT=" + display(snapshot))
    // 明示的な逐次呼出し。別threadや非同期callbackは使わない。
    mutate()
    println("CAPTURED_NOW=" + display(local))
    if (snapshot != null) {
        println("RESULT=" + snapshot.length)
    } else {
        println("RESULT=SKIPPED")
    }
}

fun main(args: Array<String>) {
    require(args.size == 2) { "modeと入力を指定してください" }
    val initial: String? = when (args[1]) {
        "ada" -> "Ada"
        "null" -> null
        else -> error("入力はadaかnullです")
    }
    when (args[0]) {
        "local-control" -> localControl(initial)
        "captured-snapshot" -> capturedSnapshot(initial)
        else -> error("未知のmode")
    }
}
