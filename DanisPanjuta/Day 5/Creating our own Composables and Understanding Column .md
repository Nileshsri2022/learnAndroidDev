Here is a structured breakdown and explanation of the concepts introduced in this lesson:

---

### 1. Creating Custom Composables (`@Composable`)
To build reusable UI components in Jetpack Compose, you define standard Kotlin functions annotated with `@Composable`:

```kotlin
@Composable
fun UnitConverter() {
    // UI elements go here
}
```

* **The `@Composable` Annotation:** Tells the Kotlin compiler that this function is meant to emit user interface elements.
* **Composability Rule:** A `@Composable` function can **only** be called from another `@Composable` function or from a `setContent { }` block.

---

### 2. Declarative UI: Composition & Recomposition
* **Composition:** The process where Jetpack Compose executes your `@Composable` functions to build and display the initial UI on the screen.
* **Recomposition:** The process where Jetpack Compose **re-executes** your composables to update the UI when the underlying data or **state** changes.
* **Declarative Approach:** Instead of manually finding and updating views (like `textView.setText(...)`), you simply describe what the UI should look like for a given data state. Compose handles refreshing the screen automatically.

---

### 3. Layout Containers: `Column` vs. `Row`

When multiple UI elements (like two `Text` components) are placed without a layout container, they will render on top of each other (overlapping) because Compose doesn't know where to position them.

To control layout flow, Compose provides standard layout containers:

#### A. `Column` (Vertical Stacking)
Places UI elements **vertically**, one below the other:

```kotlin
Column {
    Text("First item (Top)")
    Text("Second item (Bottom)")
}
```

#### B. `Row` (Horizontal Stacking)
Places UI elements **horizontally**, side by side:

```kotlin
Row {
    Text("First item (Left)")
    Text("Second item (Right)")
}
```

#### C. Combining Column and Row
You can nest `Row` containers inside a `Column` (or vice versa) to create grid-like layouts:

```kotlin
@Composable
fun UnitConverter() {
    Column {
        // UI elements stacked vertically
        Greeting(name = "Android")

        Row {
            // UI elements placed side-by-side inside this row
            Greeting(name = "Android 1")
            Greeting(name = "Android 2")
        }
    }
}
```

---

### Summary Checklist
1. **`@Composable`:** Turns a regular Kotlin function into a UI building block.
2. **Recomposition:** Automatically recalculates and redraws the UI when data/state changes.
3. **`Column`:** Stacks elements from **top to bottom**.
4. **`Row`:** Arranges elements from **left to right**.
