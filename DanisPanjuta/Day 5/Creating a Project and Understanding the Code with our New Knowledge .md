Here is a clear, structured breakdown and explanation of everything covered in your lesson on setting up and understanding a Jetpack Compose project.

---

### 1. Project Creation & Structure
* **Empty Activity:** Choosing "Empty Activity" creates a modern Jetpack Compose template (unlike older templates that used XML layouts).
* **Project View (`Android` mode):**
  * **`app/manifests`:** Contains app configuration.
  * **`app/java (or kotlin)/<your.package.name>`:** Where your main source code lives.
  * **`MainActivity.kt`:** The entry point of your app.
  * **`ui.theme/`:** Contains color schemes, typography, and theme definitions.
  * **`Gradle Scripts`:** Configuration files that build your app and manage dependencies/libraries.

---

### 2. `MainActivity` and `onCreate`
```kotlin
class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            UnitConverterTheme {
                // UI Code here
            }
        }
    }
}
```
* **`ComponentActivity`:** A core Android class that gives your app a screen/window and manages its lifecycle.
* **`override fun onCreate(...)`:** The function Android calls when your app launches. Overriding it allows you to define what happens at startup.
* **`setContent { ... }`:** A Compose function that replaces the traditional `setContentView(R.layout...)`. Everything inside this block defines the user interface (UI).

---

### 3. What is a Composable (`@Composable`)?
In Jetpack Compose, **UI elements are just Kotlin functions** marked with the `@Composable` annotation.

* Regular Kotlin functions compute data or perform actions.
* **Composable functions emit UI onto the screen.**
* You build complex screens by nesting smaller composables inside larger ones (like building with Lego blocks).

---

### 4. Theming (`UnitConverterTheme`) and Dark Mode
* **`UnitConverterTheme`:** A wrapper composable that defines colors, shapes, and typography.
* **Automatic Theme Switching:** It checks if the device is in Light Mode or Dark Mode (`isSystemInDarkTheme()`) and applies the appropriate color palette:
  * **Light Theme:** White background, black text.
  * **Dark Theme:** Dark gray/black background, white text.

---

### 5. `Surface` and `Modifier`
```kotlin
Surface(
    modifier = Modifier.fillMaxSize(),
    color = MaterialTheme.colorScheme.background
) {
    // Content inside the surface
}
```
* **`Surface`:** A basic container/canvas (like a sheet of paper) that holds other UI elements and sets their background color.
* **`Modifier`:** An object used to adjust how a composable looks and behaves (size, padding, background, click events, etc.).
  * **`Modifier.fillMaxSize()`:** Tells the `Surface` to expand and take up 100% of the screen height and width.

---

### 6. UI Composables: `Greeting` and `Text`
```kotlin
@Composable
fun Greeting(name: String, modifier: Modifier = Modifier) {
    Text(
        text = "Hello $name!",
        modifier = modifier
    )
}
```

#### Why are there so many parameters in `Text()`?
If you inspect the `Text` composable, you'll see parameters like `fontSize`, `fontStyle`, `textAlign`, `maxLines`, and `color`.
* **Default Arguments:** Most parameters have default values, meaning you only need to provide what you want to change (like `text = "Hello Android"`).
* **Data Types Used:**
  * **Primitives:** Simple types like `Boolean` (`softWrap`) or `Int` (`maxLines`).
  * **Custom Classes:** Complex types like `TextUnit` (for font size, e.g., `24.sp`) or `FontStyle` (for italic/normal).

---

### Summary Checklist of Key Takeaways
1. **Compose UI = Functions:** You build UIs using `@Composable` functions rather than XML files.
2. **`setContent` connects Android to Compose:** It defines the root UI tree.
3. **Themes handle styling automatically:** `MaterialTheme` provides colors and styles that adapt to dark/light mode.
4. **Modifiers configure UI:** Use `Modifier` to control dimensions, spacing, and layout behavior.
