// SPDX-License-Identifier: Apache-2.0
class CustomGetterBox {
    private var reads: Int = 0
    val value: String?
        get() {
            reads += 1
            return if (reads == 1) "Ada" else null
        }
}

fun lengthAfterCheck(box: CustomGetterBox): Int? {
    if (box.value != null) {
        return box.value.length
    }
    return null
}
