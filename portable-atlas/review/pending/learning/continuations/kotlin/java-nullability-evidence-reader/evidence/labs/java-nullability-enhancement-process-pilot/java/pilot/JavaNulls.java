// SPDX-License-Identifier: Apache-2.0
package pilot;

import org.jetbrains.annotations.NotNull;

public final class JavaNulls {
    private JavaNulls() {}

    public static @NotNull String stable(boolean empty) {
        return empty ? "" : "atlas";
    }

    public static @NotNull String violatesContract() {
        return null;
    }

    public static int consume(@NotNull String value) {
        return value.length();
    }
}
