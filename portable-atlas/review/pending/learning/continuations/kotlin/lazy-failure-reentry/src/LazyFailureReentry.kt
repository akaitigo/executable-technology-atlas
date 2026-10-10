// Atlas: finite single-thread fixture; no dependency on expected.json.
import kotlin.system.exitProcess

class Token(val id: Int, val marker: Int = 7)
class PlannedInitFailure : RuntimeException("Atlas planned first initialization failure")
class ReentryDepthExceeded : RuntimeException("Atlas fixture exceeded depth two")

fun json(v: Any?): String = when (v) {
    null -> "null"
    is Boolean, is Number -> v.toString()
    is String -> buildString {
        append('"')
        for (c in v) when (c) {
            '"' -> append("\\\""); '\\' -> append("\\\\")
            '\n' -> append("\\n"); '\r' -> append("\\r"); '\t' -> append("\\t")
            else -> if (c.code < 32) append("\\u%04x".format(c.code)) else append(c)
        }
        append('"')
    }
    is Map<*, *> -> v.entries.joinToString(",", "{", "}") { json(it.key.toString()) + ":" + json(it.value) }
    is Iterable<*> -> v.joinToString(",", "[", "]") { json(it) }
    else -> error("unsupported JSON value")
}
fun emit(v: Map<String, Any?>) { println(json(v)); System.out.flush() }
fun token(t: Token?): Any? = t?.let { mapOf("id" to it.id, "marker" to it.marker) }
fun exception(e: Throwable) = mapOf("type" to e.javaClass.name, "message" to e.message, "stack" to e.stackTraceToString())

fun observe(mode: LazyThreadSafetyMode, family: String): Boolean {
    val id = "$family-${mode.name.lowercase()}"
    var calls = 0
    var depth = 0
    var maxDepth = 0
    val events = mutableListOf<Map<String, Any?>>()
    val phases = mutableListOf<Map<String, Any?>>()
    val planned = mutableListOf<Map<String, Any?>>()
    val failures = mutableListOf<Map<String, Any?>>()
    val created = mutableListOf<Token>()
    val reads = linkedMapOf<String, Token>()
    lateinit var value: Lazy<Token>
    fun event(kind: String, t: Token? = null, attempt: Int? = null) {
        val e = linkedMapOf<String, Any?>("sequence" to events.size + 1, "kind" to kind,
            "calls" to calls, "depth" to depth, "attempt_id" to attempt, "token" to token(t),
            "thread" to Thread.currentThread().name)
        events += e
        emit(mapOf("kind" to "event", "case_id" to id, "event" to e))
    }
    fun phase(name: String, outcome: String, current: Token? = null) {
        val p = linkedMapOf<String, Any?>("id" to name, "calls" to calls, "initialized" to value.isInitialized(),
            "depth" to depth, "outcome" to outcome, "current" to token(current),
            "known_references" to reads.mapValues { token(it.value) }, "created_ids" to created.map { it.id },
            "planned_exceptions_so_far" to planned.toList())
        phases += p
        emit(mapOf("kind" to "phase", "case_id" to id, "phase" to p))
    }
    fun create(attempt: Int): Token {
        val t = Token(attempt)
        created += t
        event("token-created", t, attempt)
        return t
    }
    var inner: Token? = null
    var outerCreated: Token? = null
    var first: Token? = null
    var later: Token? = null
    value = lazy(mode) {
        val attempt = ++calls // Capture before nested access; never renumber from shared counter.
        depth++
        maxDepth = maxOf(maxDepth, depth)
        try {
            event("initializer-enter", attempt = attempt)
            if (depth > 2) throw ReentryDepthExceeded()
            if (family == "failure" && attempt == 1) {
                event("planned-throw", attempt = attempt)
                throw PlannedInitFailure()
            }
            if (family == "reentry" && depth == 1) {
                event("nested-read-start", attempt = attempt)
                val nested = value.value
                inner = nested
                reads["inner-getter"] = nested
                event("nested-read-return", nested, attempt)
                phase("inner-returned", "normal", nested)
            }
            val t = create(attempt)
            if (family == "reentry" && depth == 1) {
                outerCreated = t
                reads["outer-created"] = t
                reads["outer-initializer-return"] = t
            }
            event("initializer-return", t, attempt)
            t
        } finally {
            depth--
            event("initializer-exit", attempt = attempt)
        }
    }
    try {
        phase("initial", "not-read")
        if (family == "failure") {
            event("first-read-start")
            try {
                val unexpected = value.value
                event("unexpected-first-read-return", unexpected)
                error("expected first initializer exception did not occur")
            } catch (e: PlannedInitFailure) {
                planned += exception(e)
                event("expected-exception-caught")
            }
            phase("first-failure", "expected-initializer-exception")
            event("retry-read-start")
            val retry = value.value
            first = retry
            reads["retry-getter"] = retry
            event("retry-read-return", retry)
            phase("retry-success", "normal", retry)
        } else {
            event("outer-read-start")
            val outer = value.value
            first = outer
            reads["outer-getter"] = outer
            event("outer-read-return", outer)
            phase("outer-getter-returned", "normal", outer)
        }
        event("later-read-start")
        val cached = value.value
        later = cached
        reads["later-getter"] = cached
        event("later-read-return", cached)
        phase("cached-read", "normal", cached)
    } catch (e: Throwable) {
        failures += exception(e)
        emit(mapOf("kind" to "unexpected-failure", "case_id" to id, "error" to exception(e)))
    }
    val same = if (family == "failure") mapOf("successful_reads_same_reference" to (first != null && first === later))
    else mapOf("inner_same_as_outer_created" to (inner != null && inner === outerCreated),
        "first_same_as_inner" to (first != null && first === inner),
        "first_same_as_outer_created" to (first != null && first === outerCreated),
        "later_same_as_first" to (later != null && later === first),
        "outer_initializer_return_same_as_outer_created" to (reads["outer-initializer-return"] != null && reads["outer-initializer-return"] === outerCreated))
    val complete = failures.isEmpty() && depth == 0
    emit(linkedMapOf("kind" to "case", "id" to id, "mode" to mode.name, "family" to family,
        "worker_count" to 0, "events" to events, "phases" to phases, "reads" to reads.mapValues { token(it.value) },
        "created_ids" to created.map { it.id }, "comparisons" to same, "planned_exceptions" to planned,
        "calls_total" to calls, "max_depth" to maxDepth, "final_depth" to depth,
        "failures" to failures, "collection_complete" to complete))
    return complete
}

fun main() {
    emit(mapOf("kind" to "environment", "project" to "Atlas", "java_version" to System.getProperty("java.version"),
        "kotlin_version" to KotlinVersion.CURRENT.toString(), "available_processors" to Runtime.getRuntime().availableProcessors(),
        "max_heap_bytes" to Runtime.getRuntime().maxMemory(), "thread" to Thread.currentThread().name))
    for (family in listOf("failure", "reentry"))
        for (mode in listOf(LazyThreadSafetyMode.SYNCHRONIZED, LazyThreadSafetyMode.PUBLICATION, LazyThreadSafetyMode.NONE))
            if (!observe(mode, family)) exitProcess(1)
    emit(mapOf("kind" to "batch-complete", "case_count" to 6, "retry_count" to 0, "worker_count" to 0))
}
