// Atlas KR-03: bounded JVM observations, independent of expected.json.
import java.util.Collections
import java.util.concurrent.Callable
import java.util.concurrent.CountDownLatch
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.Future
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException
import java.util.concurrent.atomic.AtomicInteger
import kotlin.system.exitProcess

data class Token(val id: Int, val marker: Int)
data class Case(val id: String, val mode: LazyThreadSafetyMode, val workers: Int)

fun json(value: Any?): String = when (value) {
    null -> "null"
    is Boolean, is Number -> value.toString()
    is String -> buildString {
        append('"')
        for (c in value) when (c) {
            '"' -> append("\\\"")
            '\\' -> append("\\\\")
            '\n' -> append("\\n")
            '\r' -> append("\\r")
            '\t' -> append("\\t")
            else -> if (c.code < 32) append("\\u%04x".format(c.code)) else append(c)
        }
        append('"')
    }
    is Map<*, *> -> value.entries.joinToString(",", "{", "}") { json(it.key.toString()) + ":" + json(it.value) }
    is Iterable<*> -> value.joinToString(",", "[", "]") { json(it) }
    else -> error("unsupported record value: ${value.javaClass.name}")
}

fun emit(value: Map<String, Any?>) { println(json(value)); System.out.flush() }

fun observe(c: Case): Boolean {
    val count = AtomicInteger(0)
    val events = mutableListOf<Map<String, Any?>>()
    fun event(kind: String, reader: String? = null, token: Token? = null, attempt: Int? = null) = synchronized(events) {
        events += linkedMapOf("sequence" to events.size + 1, "kind" to kind, "thread" to Thread.currentThread().name,
            "reader" to reader, "attempt_id" to attempt, "token_id" to token?.id, "marker" to token?.marker)
    }
    val value = lazy(c.mode) {
        val attempt = count.incrementAndGet()
        event("initializer-enter", attempt = attempt)
        val token = Token(attempt, 7)
        event("initializer-return", token = token, attempt = attempt)
        token
    }
    val record = linkedMapOf<String, Any?>("kind" to "case", "id" to c.id, "mode" to c.mode.name,
        "workers" to c.workers, "initial_count" to count.get(), "initial_initialized" to value.isInitialized())
    val results = mutableListOf<Pair<String, Token>>()
    val failures = mutableListOf<Map<String, String>>()
    var executor: ExecutorService? = null
    val futures = mutableListOf<Future<Token>>()
    val start = CountDownLatch(1)
    val ready = CountDownLatch(c.workers)
    val createdWorkers = AtomicInteger(0)
    val workerNames = Collections.synchronizedList(mutableListOf<String>())
    var terminated: Boolean? = null
    var releasedByMain = false
    val begin = System.nanoTime()
    val deadline = begin + TimeUnit.SECONDS.toNanos(2)
    fun remaining(): Long {
        val nanos = deadline - System.nanoTime()
        if (nanos <= 0) throw TimeoutException("case absolute deadline")
        return nanos
    }
    fun read(reader: String): Token {
        event("read-start", reader)
        val result = value.value
        event("read-return", reader, result)
        return result
    }
    try {
        if (c.workers == 0) {
            results += "main-1" to read("main-1")
            results += "main-2" to read("main-2")
        } else {
            executor = Executors.newFixedThreadPool(2) { job ->
                val name = "atlas-${c.id}-${createdWorkers.incrementAndGet()}"
                workerNames += name
                Thread(job, name)
            }
            for (index in 1..2) futures += executor.submit(Callable {
                val reader = "worker-$index"
                event("worker-ready", reader)
                ready.countDown()
                if (!start.await(remaining(), TimeUnit.NANOSECONDS)) throw TimeoutException("worker start timeout")
                read(reader)
            })
            if (!ready.await(remaining(), TimeUnit.NANOSECONDS)) throw TimeoutException("ready timeout")
            event("start-release")
            releasedByMain = true
            start.countDown()
            for ((index, future) in futures.withIndex()) results += "worker-${index + 1}" to future.get(remaining(), TimeUnit.NANOSECONDS)
            event("workers-returned")
            results += "main-after-workers" to read("main-after-workers")
        }
    } catch (error: Throwable) {
        failures += mapOf("stage" to "observation", "type" to error.javaClass.name, "detail" to error.stackTraceToString())
    } finally {
        start.countDown()
        for (future in futures) try { if (!future.isDone) future.cancel(true) } catch (error: Throwable) {
            failures += mapOf("stage" to "cancel", "type" to error.javaClass.name, "detail" to error.toString())
        }
        if (executor != null) {
            try { executor.shutdownNow() } catch (error: Throwable) {
                failures += mapOf("stage" to "shutdown", "type" to error.javaClass.name, "detail" to error.toString())
            }
            try { terminated = executor.awaitTermination(1, TimeUnit.SECONDS) } catch (error: Throwable) {
                failures += mapOf("stage" to "awaitTermination", "type" to error.javaClass.name, "detail" to error.toString())
                terminated = false
            }
            if (terminated != true) failures += mapOf("stage" to "cleanup", "type" to "UnreapedExecutor", "detail" to "No next case may start")
        }
    }
    val first = results.firstOrNull()?.second
    record["reads"] = results.map { (reader, token) -> linkedMapOf("reader" to reader, "id" to token.id, "marker" to token.marker, "same_reference_as_first" to (token === first)) }
    record["count_after"] = count.get()
    record["initialized_after"] = value.isInitialized()
    record["events"] = synchronized(events) { events.toList() }
    record["created_workers"] = createdWorkers.get()
    record["worker_names"] = synchronized(workerNames) { workerNames.toList() }
    record["start_released_after_ready"] = releasedByMain
    record["futures_done"] = futures.map { it.isDone }
    record["executor_terminated"] = terminated
    record["failures"] = failures
    record["elapsed_nanos"] = System.nanoTime() - begin
    record["collection_complete"] = failures.isEmpty()
    emit(record)
    return failures.isEmpty()
}

fun main() {
    emit(linkedMapOf("kind" to "environment", "project" to "Atlas", "java_version" to System.getProperty("java.version"),
        "java_vendor" to System.getProperty("java.vendor"), "kotlin_version" to KotlinVersion.CURRENT.toString(),
        "available_processors" to Runtime.getRuntime().availableProcessors(), "max_heap_bytes" to Runtime.getRuntime().maxMemory()))
    val cases = listOf(Case("seq-synchronized", LazyThreadSafetyMode.SYNCHRONIZED, 0),
        Case("seq-publication", LazyThreadSafetyMode.PUBLICATION, 0), Case("seq-none", LazyThreadSafetyMode.NONE, 0),
        Case("concurrent-synchronized", LazyThreadSafetyMode.SYNCHRONIZED, 2), Case("concurrent-publication", LazyThreadSafetyMode.PUBLICATION, 2))
    for (case in cases) if (!observe(case)) exitProcess(1)
    emit(mapOf("kind" to "batch-complete", "case_count" to cases.size, "retry_count" to 0))
}
