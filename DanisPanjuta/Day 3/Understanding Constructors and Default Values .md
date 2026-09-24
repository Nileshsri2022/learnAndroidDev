Here is a clear, structured explanation of the concepts covered in this video.

---

### **Overview: What is This Lesson About?**
This lesson explains how to give your classes **characteristics (data)** using **Primary Constructors** and **Properties** in Kotlin, how to access that data using **dot notation**, and how to provide **default values**.

---

### **1. Parameters vs. Properties (The `val`/`var` Difference)**

When you put arguments in the class header `class Dog(...)`, whether you include `val`/`var` changes how Kotlin treats that variable:

#### **A. Without `val` or `var` → It is just a Parameter**
```kotlin
class Dog(name: String) // Parameter only
```
* **What it is:** Temporary data passed into the class when creating it.
* **Limitation:** It is *only* available inside the class during initialization (`init` block). 
* **You CANNOT do:** `daisy.name` from outside the class (an error will occur).

#### **B. With `val` or `var` → It becomes a Property**
```kotlin
class Dog(val name: String, val breed: String) // Properties!
```
* **What it is:** A permanent characteristic stored directly in that dog object.
* **Advantage:** Kotlin automatically creates the field and makes it accessible from the outside.
* **You CAN do:** `daisy.name` and `daisy.breed`.

> **Note:** Use `val` for read-only (immutable) properties and `var` if the property will change later (mutable).

---

### **2. Accessing Properties (Dot Notation)**

Once a variable is declared with `val` or `var` in the constructor, you can access it anywhere using **dot notation** (`object.property`):

```kotlin
val daisy = Dog("Daisy", "Dwarf Poodle")

println(daisy.name)  // Prints: Daisy
println(daisy.breed) // Prints: Dwarf Poodle
```

---

### **3. String Interpolation with Object Properties**

In Kotlin:
* For a simple variable, you use `$variable`: 
  ```kotlin
  val name = "Daisy"
  println("Hello $name")
  ```
* For an **object's property** (or any expression with a dot), you **must** wrap it in curly braces `${object.property}`:
  ```kotlin
  // Correct:
  println("${daisy.name} is a ${daisy.breed}")

  // Incorrect (Kotlin thinks you only mean $daisy):
  // println("$daisy.name is a $daisy.breed") 
  ```

---

### **4. Default Values in Constructors**

You can assign a default value to a constructor property using `= value`. If a value isn't provided when creating the object, Kotlin falls back to this default.

```kotlin
class Dog(
    val name: String, 
    val breed: String, 
    var age: Int = 0 // Default value is 0
)
```

#### **How it behaves:**
1. **Without supplying the age (uses default):**
   ```kotlin
   val puppy = Dog("Daisy", "Dwarf Poodle")
   println(puppy.age) // Prints: 0
   ```
2. **Supplying the age (overrides default):**
   ```kotlin
   val adultDog = Dog("Daisy", "Dwarf Poodle", 3)
   println(adultDog.age) // Prints: 3
   ```

---

### **Complete Code Summary**

#### **`Dog.kt`**
```kotlin
class Dog(
    val name: String,
    val breed: String,
    var age: Int = 0
) {
    init {
        bark(name)
    }

    fun bark(name: String) {
        println("$name says woof woof")
    }
}
```

#### **`Main.kt`**
```kotlin
fun main() {
    // 1. Create dog with default age (0)
    val daisy = Dog("Daisy", "Dwarf Poodle")
    println("${daisy.name} is a ${daisy.breed} and is ${daisy.age} years old.")
    // Output:
    // Daisy says woof woof
    // Daisy is a Dwarf Poodle and is 0 years old.

    // 2. Create dog with custom age (overriding default)
    val rocky = Dog("Rocky", "German Shepherd", 2)
    println("${rocky.name} is a ${rocky.breed} and is ${rocky.age} years old.")
    // Output:
    // Rocky says woof woof
    // Rocky is a German Shepherd and is 2 years old.
}
```

---

### **Key Takeaways**
1. **Primary Constructor:** Declared right next to the class name: `class Dog(...)`.
2. **`val` / `var` in the constructor:** Automatically turns parameters into accessible properties of that class.
3. **`${object.property}`:** Required when referencing object properties inside string templates.
4. **`property: Type = defaultValue`:** Allows optional constructor arguments.
