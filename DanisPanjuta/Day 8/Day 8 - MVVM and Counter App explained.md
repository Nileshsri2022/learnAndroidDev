# Day 8 — MVVM, inheritance, interfaces and the counter app

Based on [`transcripts/08-Day 8 - MVVM - Model View ViewModel - Architecture - Counter App Part 2`](../transcripts/08-Day%208%20-%20MVVM%20-%20Model%20View%20ViewModel%20-%20Architecture%20-%20Counter%20App%20Part%202/). Read the numbered sections in lecture order; this is an explanation, not a verbatim transcript.

## 01–02 · Why introduce MVVM?

Earlier apps put UI and behavior together in an Activity or composable. That is quick for a small example, but harder to change and test as the app grows. **Model–View–ViewModel** separates responsibilities:

| Part | In this lesson | Responsibility |
| --- | --- | --- |
| Model | `CounterModel` | Represent the count as data. |
| View | `CounterApp` composable, hosted by `MainActivity` | Show the count and send button clicks. |
| ViewModel | `CounterViewModel` | Expose observable UI state and handle UI actions through the data layer. |
| Repository (supporting layer) | `CounterRepository` | Provide a consistent interface to the count's data source. |

The royal-orchestra story compares the ViewModel to a conductor: user actions come in, data is consulted or changed, and the view reflects the resulting state. It is an analogy, not a requirement that every app have all these files.

## 03 · First build: a counter inside the composable

A `CounterApp` can hold `remember { mutableStateOf(0) }`, display `count.value`, and wire Increment and Decrement buttons to change it. A `Column` centered with `Arrangement.Center` and `Alignment.CenterHorizontally` holds the text, a `Spacer`, and a `Row` of buttons. `24.sp` changes text size; `16.dp` adds spacing.

`remember` retains state across **recomposition**, but an orientation change normally recreates the Activity, so this locally remembered count resets. Try tapping Increment several times and rotating the device to see the problem. `rememberSaveable` is another valid solution for small saveable UI state; a ViewModel is useful here mainly to teach architecture and to retain state through configuration changes.

## 04 · Move state and actions into a ViewModel

Create `CounterViewModel : ViewModel()` (AndroidX Lifecycle). Keep writable state private, expose read-only `State<Int>`, and make the UI call functions rather than mutate the count itself:

```kotlin
import androidx.compose.runtime.State
import androidx.compose.runtime.mutableStateOf
import androidx.lifecycle.ViewModel

class CounterViewModel : ViewModel() {
    private val _count = mutableStateOf(0)
    val count: State<Int> = _count

    fun increment() { _count.value++ }
    fun decrement() { _count.value-- }
}
```

Then `CounterApp(viewModel: CounterViewModel)` reads `viewModel.count.value`; the buttons call `viewModel.increment()` and `viewModel.decrement()`. In a composable host, obtain the instance with the lifecycle-aware `viewModel<CounterViewModel>()` function from `androidx.lifecycle.viewmodel.compose`, then pass it to `CounterApp`. Do **not** construct a fresh `CounterViewModel()` on every recomposition. The lifecycle-scoped instance survives a normal rotation, but **not process death**; for that use saved state (`SavedStateHandle`/`rememberSaveable`) or persistent storage as appropriate.

`val count: State<Int> = _count` exposes the *same observable state*, not a one-time copy of its initial value. The UI can observe updates but cannot set `count.value` through this read-only type. A plain `val count = mutableStateOf(_count.value)` would instead create a disconnected snapshot.

## 05–06 · Why `ViewModel()` and `override` work

Kotlin inheritance uses a colon: `class Child : Parent()`. A user-defined parent class must be marked `open` to allow subclassing. An inherited method is available on a child even when not declared again there. To change it, mark the parent method `open` and the child implementation `override`:

```kotlin
open class House {
    fun coreValues() = println("Shared values")
    open fun role() = println("Member")
}
class Knight : House() {
    override fun role() {
        super.role() // optional: call the parent's implementation
        println("Knight")
    }
}
```

`Knight().coreValues()` works through inheritance. `Knight().role()` prints both lines; remove `super.role()` to replace the parent's behavior entirely. This helps explain the familiar `MainActivity : ComponentActivity()` and `override fun onCreate(...)` pattern. Kotlin classes and methods are final by default unless designed for inheritance (or already overridable in a framework).

## 07–08 · Interfaces: capabilities and contracts

The lecture's archer/singer and guild stories illustrate that one class can inherit **one class** but implement **multiple interfaces**. An interface states what operations are available; implementers can provide different behavior. It can also provide default implementations:

```kotlin
interface Archer { fun shoot() }
interface Singer { fun sing() }
open class Knight : House()
class Performer : Knight(), Archer, Singer {
    override fun shoot() = println("Arrow!")
    override fun sing() = println("Song!")
}
```

Unlike a class superclass, interfaces appear without constructor parentheses. Abstract interface functions must be implemented; a default function body can be overridden, and `super<Archer>.someFunction()` calls that interface's default implementation when needed. Interfaces make collaborators interchangeable by contract, without exposing their implementation details.

## 09 · Add a model and repository

The transcript next introduces `CounterModel(count: Int)` and a `CounterRepository` that owns the count, with `getCounter()`, `incrementCounter()` and `decrementCounter()`. One consistent way to implement that example is:

```kotlin
data class CounterModel(val count: Int)

class CounterRepository {
    private var counter = CounterModel(0)
    fun getCounter(): CounterModel = counter
    fun incrementCounter() { counter = counter.copy(count = counter.count + 1) }
    fun decrementCounter() { counter = counter.copy(count = counter.count - 1) }
}

class CounterViewModel : ViewModel() {
    private val repository = CounterRepository()
    private val _count = mutableStateOf(repository.getCounter().count)
    val count: State<Int> = _count

    fun increment() {
        repository.incrementCounter()
        _count.value = repository.getCounter().count
    }
    fun decrement() {
        repository.decrementCounter()
        _count.value = repository.getCounter().count
    }
}
```

The composable interface from section 04 stays unchanged. The repository manages data; the ViewModel turns it into observable UI state. `copy` is necessary here because `count` is a `val` in the data class. The lecture simplifies setup by creating the repository inside the ViewModel; injecting it through a constructor is often better for tests, but requires a ViewModel factory or dependency-injection setup. An in-memory repository also resets on process death.

## 10 · Why the extra layer?

A repository can hide whether data comes from memory, a database or an API. That makes storage changes and isolated tests easier, and keeps the view from depending on raw data access. MVVM likewise separates UI, presentation logic and data. For this tiny counter it is more structure than necessary; the benefit becomes clearer in larger apps. The chef/supplier analogy in the transcript describes the repository as the supplier of ingredients, though in actual MVVM the **ViewModel**, not the View, should usually coordinate with that supplier.

## 11–13 · Wrap-up and practice

The closing lecture recaps inheritance, interfaces, ViewModel and repository, then previews API calls in Day 9. Lectures 12 (summary) and 13 (cheatsheet) have **no transcript available**, so there is no additional lesson content to explain here.

**Try it:** Run the local-state version, increment and rotate; then switch to the ViewModel version and repeat. Explain which object survives rotation, which observes the changing count, and what would happen if Android killed the app process. As a further exercise, replace the in-memory repository with a persistent source while leaving the composable API unchanged.
