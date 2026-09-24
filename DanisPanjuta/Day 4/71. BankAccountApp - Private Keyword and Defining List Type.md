Here is a clear, structured breakdown of the concepts explained in this lesson.

---

### **Overview: What is This Lesson About?**
This lesson begins building a practical **Bank Account Program** in Kotlin. It brings together Object-Oriented Programming (OOP) concepts by designing a class that bundles **data** (account holder, balance, transaction history) with **behaviors** (deposit, withdraw, display history).

It introduces two fundamental concepts:
1. **Encapsulation** using the **`private`** visibility modifier.
2. **Explicit Type Declaration** when creating empty collections (`mutableListOf<String>()`).

---

### **1. Encapsulation & The `private` Keyword**

**Encapsulation** is a core OOP principle: you protect the internal state of an object and only allow it to be modified through controlled actions (functions).

```kotlin
// Public (Default): Accessible from anywhere
val accountHolder: String

// Private: Accessible ONLY from inside this BankAccount class
private val transactionHistory = mutableListOf<String>()
```

#### **Why make `transactionHistory` private?**
* **Security & Integrity:** You don't want outside code directly modifying, deleting, or corrupting the bank's transaction records (e.g., `dennisAccount.transactionHistory.clear()`).
* **Controlled Access:** Instead of exposing the raw list, the class provides a safe, controlled function: `displayTransactionHistory()`.

| Visibility Modifier | Accessible Inside Class? | Accessible Outside (e.g., in `main()`)? |
| :--- | :---: | :---: |
| **`public`** (default in Kotlin) |  Yes |  Yes (`account.accountHolder`) |
| **`private`** |  Yes | ❌ No (Compilation Error) |

---

### **2. Explicit Type Declaration in Empty Lists**

In Kotlin, **Type Inference** allows the compiler to automatically guess a variable's type based on its initial value:
* `val name = "Dennis"` $\rightarrow$ inferred as `String`
* `val numbers = listOf(1, 2, 3)` $\rightarrow$ inferred as `List<Int>`

However, when you create an **empty list**, Kotlin cannot guess what will be placed in it later:

```kotlin
//  Error: Kotlin does not know what type of items this list will hold
val list = mutableListOf() 

//  Correct: Explicitly tell Kotlin this list holds Strings
val transactionHistory = mutableListOf<String>()
```

---

### **3. Code Structure So Far**

Here is the setup created in the video:

#### **File: `BankAccount.kt`**
```kotlin
class BankAccount(
    var accountHolder: String,
    var balance: Double
) {
    // Private property: hidden from the outside world
    private val transactionHistory = mutableListOf<String>()

    // Member functions representing actions (to be implemented next)
    fun deposit(amount: Double) {
        // Logic to add money and record transaction
    }

    fun withdraw(amount: Double) {
        // Logic to subtract money and record transaction
    }

    fun displayTransactionHistory() {
        // Safe way to show history without exposing the raw list
    }
}
```

#### **File: `BankMain.kt`**
```kotlin
fun main() {
    // 1. Create a bank account instance
    val dennisAccount = BankAccount("Dennis Panjuta", 1343.50)

    // 2. Access public properties (Allowed)
    println("Account Holder: ${dennisAccount.accountHolder}")
    println("Current Balance: $${dennisAccount.balance}")

    // 3. Attempting to access a private property (Will NOT compile):
    // dennisAccount.transactionHistory //  ERROR: Cannot access 'transactionHistory': it is private in 'BankAccount'
}
```

---

### **Key Takeaways**
1. **`private`** hides variables or functions so they can only be used inside the class where they are declared.
2. **Encapsulation** protects sensitive data by restricting direct access and using member functions to interact with it safely.
3. **`mutableListOf<Type>()`** requires specifying `<Type>` in angle brackets when initializing an empty list because type inference has no starting elements to evaluate.
4. **`Double`** is used for currency/balances to support decimal values (e.g., `1343.50`).
