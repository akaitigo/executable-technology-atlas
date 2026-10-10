// SPDX-License-Identifier: Apache-2.0
class MutableBox(var value: String?)

fun lengthAfterCheck(box: MutableBox): Int? {
    if (box.value != null) {
        return box.value.length
    }
    return null
}
