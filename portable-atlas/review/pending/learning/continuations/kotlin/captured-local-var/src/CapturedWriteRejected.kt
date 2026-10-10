// SPDX-License-Identifier: Apache-2.0
fun lengthAfterCapturedWrite(initial: String?): Int? {
    var local: String? = initial
    val mutate: () -> Unit = {
        local = if (local == null) "Ada" else null
    }
    if (local != null) {
        mutate()
        return local.length
    }
    return null
}
