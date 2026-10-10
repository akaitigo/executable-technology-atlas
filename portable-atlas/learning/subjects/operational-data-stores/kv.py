#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""A bounded integer-valued KV API; SQL is executed by an injected session recorder."""
READ = "SELECT value, version FROM kv WHERE key = ?"
CAS = "UPDATE kv SET value = ?, version = version + 1 WHERE key = ? AND version = ?"
BLIND = "UPDATE kv SET value = ?, version = version + 1 WHERE key = ?"
MAX_INT = 2**63 - 1


def compare_and_swap(session, key, value, expected_version):
    if not isinstance(key, str) or not key:
        return session.reject(key, value, expected_version, "key must be nonempty str")
    if type(expected_version) is not int or not 0 <= expected_version < MAX_INT:
        return session.reject(key, value, expected_version, "expected_version must be bounded nonnegative int; bool is rejected")
    if type(value) is not int or not -MAX_INT-1 <= value <= MAX_INT:
        return session.reject(key, value, expected_version, "value must be signed 64-bit int; bool is rejected")
    return session.execute("cas", CAS, [value, key, expected_version])
