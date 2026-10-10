"""Independent fixed authorization/time oracle; no imports from model."""
ALLOWED = {'initial': frozenset(['v1']), 'overlap': frozenset(['v1', 'v2']), 'revoked': frozenset(['v2'])}
ISSUER = {'initial': 'v1', 'overlap': 'v2', 'revoked': 'v2'}
def expected(phase, version, now, fault):
    if fault == 'input': return 'input'
    if fault == 'unknown': return 'unknown-key'
    if version not in ALLOWED[phase]: return 'revoked'
    if fault == 'tamper': return 'tamper'
    if now >= 110: return 'expired'
    return 'accept'
# RFC 4231 §4.2, fixed externally published expected SHA256 HMAC.
RFC_MAC = 'b0344c61d8db38535ca8afceaf0bf12b881dc200c9833da726e9376c2e32cff7'
