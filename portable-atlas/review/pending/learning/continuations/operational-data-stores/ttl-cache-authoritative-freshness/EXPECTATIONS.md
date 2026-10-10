# TTL/cache hand contract

Single key item; initial SQL red/version1. Fake integer clock 0..20, monotone nondecreasing. TTL strict integer1..10 (bool refused). Events read/update/invalidate max8, closed schema. All validation before SQLite creation. Unknown key refuses.

Normal hit iff t<expires_at; fault inclusive uses <=. Fill/refill sets deadline t+TTL (not original expiry+TTL). Source update has no implicit notification. Explicit invalidate only empties cache. Same value update increments version. Harness sees SQL source; cache client never receives that audit on a hit.

Main manual table:
|t|event|source|cache after|return|kind|harness version/value stale|
|---|---|---|---|---|---|---|
|0|read|red/v1|red/v1 expires5|red/v1|MISS|false/false|
|2|update|blue/v2|red/v1 expires5|none|SOURCE_UPDATE|not applicable|
|4|read|blue/v2|red/v1 expires5|red/v1|HIT|true/true|
|5|read|blue/v2|blue/v2 expires10|blue/v2|MISS|false/false|
|6|read|blue/v2|blue/v2 expires10|blue/v2|HIT|false/false|

Inclusive fault t5 HIT old red/v1, deadlineExpired=true; t6 MISS blue/v2 new expiry11. Deadline expiration and source version mismatch are separate fields. Every fixed/custom literal row is in oracle.json/custom-oracle.json before producer. Columns: t,op,sourceValue,sourceVersion,cacheValue,cacheVersion,expiresAt,returnedValue,returnedVersion,result,versionStaleHarness,valueStaleHarness,returnedDeadlineExpired,clientSourceSelects,updateRowcount. Empty cache/events has no read/return and no hit denominator.

Fake clock is not real-clock observation. Sequential memory-only SQLite, one connection; no Redis, Cloudflare, race, eviction/stampede or whole cache guarantee. UTC records process execution only, not cache time.
