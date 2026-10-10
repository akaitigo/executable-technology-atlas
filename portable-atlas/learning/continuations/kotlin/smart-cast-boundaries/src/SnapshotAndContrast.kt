// SPDX-License-Identifier: Apache-2.0
private fun display(value: String?): String = value ?: "<null>"

private class MutableText(var value: String?)

private class ReadChangingText(private val first: String?) {
    var reads: Int = 0
        private set

    val value: String?
        get() {
            reads += 1
            val result: String? = if (reads == 1) first else null
            println("GET#" + reads + "=" + display(result))
            return result
        }
}

private fun mutableSnapshot(initial: String?) {
    val source = MutableText(initial)
    println("SOURCE_INITIAL=" + display(source.value))
    val snapshot: String? = source.value
    // 明示的な逐次変更。別threadや偶然の競合は使わない。
    source.value = if (initial == null) "Ada" else null
    println("SOURCE_NOW=" + display(source.value))
    if (snapshot != null) {
        println("SNAPSHOT=" + display(snapshot))
        println("RESULT=" + snapshot.length)
    } else {
        println("SNAPSHOT=<null>")
        println("RESULT=SKIPPED")
    }
}

private fun getterSnapshot(initial: String?) {
    val source = ReadChangingText(initial)
    val snapshot: String? = source.value
    if (snapshot != null) {
        println("SNAPSHOT=" + display(snapshot))
        println("RESULT=" + snapshot.length)
    } else {
        println("SNAPSHOT=<null>")
        println("RESULT=SKIPPED")
    }
    // 判定と利用が終わってから、別の読取りをして値の違いを見せる。
    println("NEXT_READ=" + display(source.value))
    println("READS=" + source.reads)
}

private fun getterRepeatedAssertion(initial: String?) {
    val source = ReadChangingText(initial)
    if (source.value != null) {
        println("GUARD=non-null")
        // 対照：smart castを強制するのではない。再読取りの値に!!を適用する。
        println("RESULT=" + source.value!!.length)
    } else {
        println("GUARD=null")
        println("RESULT=SKIPPED")
    }
    println("READS=" + source.reads)
}

fun main(args: Array<String>) {
    require(args.size == 2) { "modeと入力を指定してください" }
    val initial: String? = when (args[1]) {
        "ada" -> "Ada"
        "null" -> null
        else -> error("入力はadaかnullです")
    }
    when (args[0]) {
        "mutable-snapshot" -> mutableSnapshot(initial)
        "getter-snapshot" -> getterSnapshot(initial)
        "getter-repeated-assertion" -> getterRepeatedAssertion(initial)
        else -> error("未知のmode")
    }
}
