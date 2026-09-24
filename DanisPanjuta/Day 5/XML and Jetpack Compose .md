Ella’s story introduces the shift from **XML-based Android UI** to **Jetpack Compose**.

With the traditional View system, you define much of the layout in XML and use Kotlin to work with those views. With Compose, you describe the UI directly in Kotlin using functions marked `@Composable`:

```kotlin
@Composable
fun Greeting() {
    Text("Hello, Ella!")
}
```

Compose is **declarative**: you describe what the screen should look like for its current state. When observable state changes, Compose updates the affected UI, rather than requiring you to manually change each view.

The key takeaway is that Compose offers a different, often more convenient way to build Android interfaces—not that XML has stopped working. Google recommends Compose for new native Android UI, but XML remains useful in existing apps, and the two can be used together. Flutter’s widgets follow a similar declarative idea, though Flutter and Compose are separate toolkits.
