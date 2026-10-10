// Atlas: finite member-property delegation; main thread only.
import kotlin.reflect.KProperty

interface Owner {
    val id: String
    var label: String
}

class Journal {
    val events = mutableListOf<String>()
    val accessOwners = mutableListOf<Owner>()
    val bindingOwners = mutableListOf<Owner>()
    val propertyNames = mutableListOf<String>()
}

class Slot(val id: String, private val journal: Journal) {
    private var value = "A"
    private var gets = 0
    private var sets = 0
    operator fun getValue(owner: Owner, property: KProperty<*>): String {
        gets += 1
        journal.accessOwners.add(owner)
        journal.propertyNames.add(property.name)
        journal.events.add("get:${owner.id}:${property.name}:$id:$value")
        return value
    }
    operator fun setValue(owner: Owner, property: KProperty<*>, next: String) {
        sets += 1
        journal.accessOwners.add(owner)
        journal.propertyNames.add(property.name)
        journal.events.add("set:${owner.id}:${property.name}:$id:$value->$next")
        value = next
    }
    // Audit the Slot's own fields. Do not read Owner.label to create a snapshot.
    fun audit(ownerId: String): Map<String, Any?> = linkedMapOf(
        "owner" to ownerId, "slot" to id, "value" to value, "gets" to gets, "sets" to sets)
    fun counts(): Pair<Int, Int> = gets to sets
}

class DirectHolder(override val id: String, val slot: Slot) : Owner {
    override var label: String by slot
}

class Provider(private val shared: Boolean, private val journal: Journal) {
    val bindings = mutableListOf<Pair<Owner, Slot>>()
    operator fun provideDelegate(owner: Owner, property: KProperty<*>): Slot {
        val slot = if (shared && bindings.isNotEmpty()) bindings[0].second
                   else Slot("S${bindings.size + 1}", journal)
        bindings.add(owner to slot)
        journal.bindingOwners.add(owner)
        journal.propertyNames.add(property.name)
        journal.events.add("bind:${owner.id}:${property.name}:${slot.id}")
        return slot
    }
}

class ProvidedHolder(override val id: String, val provider: Provider) : Owner {
    override var label: String by provider
}

fun encode(value: Any?): String = when (value) {
    null -> "null"
    is String -> "\"" + value.replace("\\", "\\\\").replace("\"", "\\\"")
        .replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t") + "\""
    is Number, is Boolean -> value.toString()
    is Map<*, *> -> value.entries.joinToString(",", "{", "}") { encode(it.key.toString()) + ":" + encode(it.value) }
    is Iterable<*> -> value.joinToString(",", "[", "]") { encode(it) }
    else -> error("Unsupported JSON value type")
}

fun runCase(id: String): Map<String, Any?> {
    val journal = Journal()
    val h1: Owner
    val h2: Owner
    val s1: Slot
    val s2: Slot
    val providerSame: Boolean?
    val bindingMatches: Boolean?
    if (id == "direct-fresh") {
        s1 = Slot("S1", journal)
        s2 = Slot("S2", journal)
        h1 = DirectHolder("H1", s1)
        h2 = DirectHolder("H2", s2)
        providerSame = null
        bindingMatches = null
    } else {
        val provider = Provider(id == "provided-shared", journal)
        val first = ProvidedHolder("H1", provider)
        val second = ProvidedHolder("H2", provider)
        h1 = first
        h2 = second
        s1 = provider.bindings[0].second
        s2 = provider.bindings[1].second
        providerSame = first.provider === second.provider
        // Compare completed holder references only after both constructors return.
        bindingMatches = provider.bindings[0].first === h1 && provider.bindings[1].first === h2
    }
    val sameSlot = s1 === s2
    val snapshots = mutableListOf<Map<String, Any?>>()
    fun snapshot(stage: String, returned: String?) {
        snapshots.add(linkedMapOf(
            "stage" to stage, "returned" to returned,
            "bind_calls" to journal.bindingOwners.size,
            "slots_same_reference" to sameSlot,
            "owners" to listOf(s1.audit(h1.id), s2.audit(h2.id)),
            "events" to journal.events.toList()))
    }
    snapshot("constructed", null)
    snapshot("first-read", h1.label)
    snapshot("second-read", h1.label)
    h1.label = "X"
    snapshot("write", null)
    snapshot("read-after-write", h1.label)
    val otherValue = h2.label
    snapshot("read-other-owner", otherValue)
    val uniqueSlots = if (sameSlot) listOf(s1) else listOf(s1, s2)
    val accessExpected = listOf(h1, h1, h1, h1, h2)
    val ownerMatches = journal.accessOwners.size == accessExpected.size &&
        journal.accessOwners.zip(accessExpected).all { (actual, expectedOwner) -> actual === expectedOwner }
    val independent = otherValue == "A"
    return linkedMapOf(
        "kind" to "case", "id" to id, "snapshots" to snapshots,
        "binding" to linkedMapOf(
            "provider_same_reference" to providerSame,
            "slot_same_reference" to sameSlot,
            "binding_owner_references_match" to bindingMatches,
            "access_owner_references_match" to ownerMatches,
            "property_names" to journal.propertyNames.toList()),
        "final" to linkedMapOf(
            "bind_calls" to journal.bindingOwners.size,
            "get_calls" to uniqueSlots.sumOf { it.counts().first },
            "set_calls" to uniqueSlots.sumOf { it.counts().second },
            "unique_slots" to uniqueSlots.size,
            "owner_isolation_satisfied" to independent,
            "classification" to if (independent) "normal" else "expected-design-violation",
            "runtime_exit" to 0))
}

fun main() {
    println(encode(linkedMapOf("kind" to "environment", "project" to "Atlas",
        "kotlin_version" to KotlinVersion.CURRENT.toString(),
        "java_version" to System.getProperty("java.version"),
        "os_name" to System.getProperty("os.name"), "os_arch" to System.getProperty("os.arch"),
        "thread" to Thread.currentThread().name, "workers_created" to 0)))
    for (id in listOf("direct-fresh", "provided-fresh", "provided-shared")) println(encode(runCase(id)))
    println(encode(linkedMapOf("kind" to "batch-complete", "cases" to 3, "workers_created" to 0)))
}
