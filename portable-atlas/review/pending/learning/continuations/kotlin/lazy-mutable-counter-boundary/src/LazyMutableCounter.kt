// Atlas: fixed two-worker update witnesses, not an arbitrary-schedule proof.
import java.util.concurrent.Callable
import java.util.concurrent.CountDownLatch
import java.util.concurrent.CyclicBarrier
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

class Counter {
    var plain: Int = 0
    val atomic = AtomicInteger(0)
    val updateLock = Any() // not the Lazy instance
}

data class WorkerResult(
    val worker: String, val threadId: Long, val payload: Counter,
    val storage: Any?, val lock: Any?, val old: Int?, val written: Int?,
    val returned: Int, val events: List<Map<String, Any?>>
)

fun json(value: Any?): String = when(value) {
    null -> "null"
    is String -> "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + "\""
    is Number, is Boolean -> value.toString()
    is Map<*,*> -> value.entries.joinToString(",","{","}"){json(it.key.toString())+":"+json(it.value)}
    is Iterable<*> -> value.joinToString(",","[","]"){json(it)}
    else -> error("unsupported JSON type")
}
fun remaining(deadline: Long): Long {
    val left = deadline-System.nanoTime()
    if(left<=0) throw java.util.concurrent.TimeoutException("case deadline exhausted")
    return left
}
fun runCase(id: String): Map<String,Any?> {
    val initCount=AtomicInteger(0)
    val initialization=mutableListOf<Map<String,Any?>>() // written only by synchronized initializer
    val value=lazy(LazyThreadSafetyMode.SYNCHRONIZED) {
        initCount.incrementAndGet()
        val p=Counter()
        initialization.add(linkedMapOf("event" to "constructed", "thread_id" to Thread.currentThread().id,
            "plain_initial_value" to p.plain, "atomic_initial_value" to p.atomic.get()))
        p
    }
    val before=linkedMapOf<String,Any?>("initialized" to value.isInitialized(),"initializer_calls" to initCount.get(),
        "payload_value" to null,"payload_value_observed" to false)
    val ready=CountDownLatch(2);val start=CountDownLatch(1);val boundary=CyclicBarrier(2)
    val threads=mutableListOf<Thread>();var created=0
    val pool=Executors.newFixedThreadPool(2){r -> Thread(r,"atlas-$id-${++created}").also{threads.add(it)}}
    val futures=mutableListOf<java.util.concurrent.Future<WorkerResult>>()
    val results=mutableListOf<WorkerResult>();val errors=mutableListOf<Map<String,String>>()
    val deadline=System.nanoTime()+TimeUnit.SECONDS.toNanos(2)
    var terminated=false
    try {
        for(worker in listOf("A","B")) {
            futures.add(pool.submit(Callable {
                val local=mutableListOf<Map<String,Any?>>()
                fun event(name: String, number: Int?=null){local.add(linkedMapOf("event" to name,"value" to number))}
                ready.countDown()
                if(!start.await(remaining(deadline),TimeUnit.NANOSECONDS)) throw java.util.concurrent.TimeoutException("start")
                event("start-passed")
                val p=value.value;event("payload-obtained")
                var old: Int?=null;var written: Int?=null;val returned: Int
                when(id){
                    "plain-split" -> {
                        val readValue=p.plain;old=readValue;event("read",readValue)
                        boundary.await(remaining(deadline),TimeUnit.NANOSECONDS);event("after-read-barrier-passed")
                        val next=readValue+1;written=next;p.plain=next;event("write",next);returned=next
                    }
                    "atomic-split" -> {
                        val readValue=p.atomic.get();old=readValue;event("atomic-get",readValue)
                        boundary.await(remaining(deadline),TimeUnit.NANOSECONDS);event("after-read-barrier-passed")
                        val next=readValue+1;written=next;p.atomic.set(next);event("atomic-set",next);returned=next
                    }
                    "locked-rmw" -> {
                        boundary.await(remaining(deadline),TimeUnit.NANOSECONDS);event("before-lock-barrier-passed")
                        synchronized(p.updateLock){
                            old=p.plain;event("locked-read",old)
                            written=old!!+1;p.plain=written!!;event("locked-write",written)
                        }
                        event("lock-released");returned=written!!
                    }
                    "atomic-rmw" -> {
                        boundary.await(remaining(deadline),TimeUnit.NANOSECONDS);event("before-update-barrier-passed")
                        returned=p.atomic.incrementAndGet();event("incrementAndGet-return",returned)
                    }
                    else -> error("unknown fixed case")
                }
                event("worker-complete",returned)
                WorkerResult(worker,Thread.currentThread().id,p,
                    if(id.startsWith("atomic"))p.atomic else null,
                    if(id=="locked-rmw")p.updateLock else null,old,written,returned,local.toList())
            }))
        }
        if(!ready.await(remaining(deadline),TimeUnit.NANOSECONDS)) throw java.util.concurrent.TimeoutException("ready")
        start.countDown()
        for(future in futures) results.add(future.get(remaining(deadline),TimeUnit.NANOSECONDS))
    } catch(e:Exception){
        errors.add(mapOf("type" to e.javaClass.name,"message" to (e.message?:"")))
    } finally {
        start.countDown()
        if(errors.isNotEmpty()) for(future in futures) future.cancel(true)
        pool.shutdown()
        try {
            if(!pool.awaitTermination(300,TimeUnit.MILLISECONDS)) {
                pool.shutdownNow()
                terminated=pool.awaitTermination(300,TimeUnit.MILLISECONDS)
            } else terminated=true
        } catch(e:InterruptedException){
            pool.shutdownNow();errors.add(mapOf("type" to e.javaClass.name,"message" to "interrupted during finite cleanup"))
            Thread.currentThread().interrupt()
        }
    }
    // Executor TERMINATED can be signalled before the Java Thread returns.
    // Join only our two Threads, using one finite deadline; never join(0,0).
    val joinDeadline=System.nanoTime()+TimeUnit.MILLISECONDS.toNanos(300)
    val threadJoins=mutableListOf<Map<String,Any?>>()
    for(t in threads) {
        val beforeAlive=t.isAlive
        try {
            val left=joinDeadline-System.nanoTime()
            if(beforeAlive && left>0) t.join(left/1_000_000,(left%1_000_000).toInt())
        } catch(e:InterruptedException) {
            errors.add(mapOf("type" to e.javaClass.name,"message" to "interrupted during finite owned-thread join"))
            Thread.currentThread().interrupt()
        }
        threadJoins.add(mapOf("id" to t.id,"alive_before" to beforeAlive,"alive_after" to t.isAlive))
    }
    val alive=threads.filter{it.isAlive}.map{it.name}
    if(!terminated||alive.isNotEmpty()) errors.add(mapOf("type" to "CleanupIncomplete","message" to alive.joinToString()))
    // An uncollected worker-local log is unknown, never fabricated from expectations.
    val complete=errors.isEmpty()&&results.size==2
    val mainPayload=if(complete)value.value else null
    val atomic=id.startsWith("atomic")
    val finalValue=if(mainPayload==null)null else if(atomic)mainPayload.atomic.get() else mainPayload.plain
    val workers=results.map{r -> linkedMapOf<String,Any?>("worker" to r.worker,"thread_id" to r.threadId,
        "old" to r.old,"written" to r.written,"returned" to r.returned,"update_count" to 1,"events" to r.events)}
    return linkedMapOf("kind" to "case","id" to id,"complete" to complete,"before_workers" to before,
        "initialization" to if(terminated || results.size==2) initialization.toList() else null,
        "initialization_detail_available" to (terminated || results.size==2),"workers" to workers,
        "collection_order" to results.map{it.worker},"collection_order_is_execution_order" to false,
        "initializer_calls" to initCount.get(),"initialized_after" to value.isInitialized(),
        "references" to linkedMapOf("worker_payloads_same" to if(complete)results[0].payload===results[1].payload else null,
            "main_payload_same" to if(complete)results.all{it.payload===mainPayload} else null,
            "atomic_storage_same" to if(complete&&atomic)results.all{it.storage===mainPayload!!.atomic} else null,
            "update_lock_same" to if(complete&&id=="locked-rmw")results.all{it.lock===mainPayload!!.updateLock} else null),
        "final_value" to finalValue,"classification" to if(!complete)"execution-failure" else if(finalValue==2)"normal" else "expected-lost-update",
        "errors" to errors,"cleanup" to linkedMapOf("executor_terminated" to terminated,"alive_threads" to alive,
            "thread_join_budget_ms" to 300,"thread_joins" to threadJoins,
            "created_threads" to threads.map{mapOf("id" to it.id,"name" to it.name)}))
}
fun main(){
    println(json(linkedMapOf("kind" to "environment","project" to "Atlas","kotlin_stdlib_version" to KotlinVersion.CURRENT.toString(),
        "java_version" to System.getProperty("java.version"),"os_name" to System.getProperty("os.name"),"os_arch" to System.getProperty("os.arch"),
        "main_thread_id" to Thread.currentThread().id,"max_workers" to 2)))
    for(id in listOf("plain-split","atomic-split","locked-rmw","atomic-rmw")) {
        val result=runCase(id);println(json(result))
        if(result["complete"]!=true) throw IllegalStateException("Atlas case failed; subsequent cases not started")
    }
    println(json(mapOf("kind" to "batch-complete","cases" to 4)))
}
