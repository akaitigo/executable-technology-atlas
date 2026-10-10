// SPDX-License-Identifier: Apache-2.0
import pilot.JavaNulls

fun evaluate(mode: String): Int = when (mode) {
    "normal" -> JavaNulls.stable(false).length
    "boundary" -> JavaNulls.stable(true).length
    "failure" -> JavaNulls.violatesContract().length
    else -> error("unknown-mode:$mode")
}

fun main(arguments: Array<String>) {
    require(arguments.size == 1) { "one-mode-required" }
    println("RESULT=" + evaluate(arguments.single()))
}
