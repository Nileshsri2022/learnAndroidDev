Here is a clear, structured breakdown of the completed **Bank Account Program** and the concepts explained in this lesson.

---

### **Overview: What is This Lesson About?**
This lesson completes the `BankAccount` class by implementing the business logic for:
1. **Depositing money** (increasing the balance & recording the transaction).
2. **Withdrawing money** with validation (preventing overdrafts using an `if-else` check).
3. **Displaying history** using a `for` loop over the private `transactionHistory` list.
4. Testing all actions in `main()` and examining **floating-point precision**.

---

### **1. Function Implementations Explained**

#### **A. `deposit(amount: Double)`**
* **Balance Update:** Uses `balance += amount` (shorthand for `balance = balance + amount`).
* **Record Keeping:** Adds a new string record into the `transactionHistory` list.
* **Double Dollar Sign (`$$amount`):** 
  * The first `$` is treated as a literal currency symbol.
  * The second `$` tells Kotlin to evaluate the variable `$amount`.

```kotlin
fun deposit(amount: Double) {
    balance += amount
    transactionHistory.add("$accountHolder deposited $$amount")
}
```

---

#### **B. `withdraw(amount: Double)` (With Funds Validation)**
Before deducting any money, we check if the account has enough funds using an `if` statement:
* **Condition Met (`amount <= balance`):** Money is deducted via `balance -= amount`, and the transaction is recorded.
* **Insufficient Funds (`else`):** The transaction is rejected, and an alert is printed to the console.

```kotlin
fun withdraw(amount: Double) {
    if (amount <= balance) {
        balance -= amount
        transactionHistory.add("$accountHolder withdrew $$amount")
    } else {
        println("You don't have the funds to withdraw $$amount")
    }
}
```

---

#### **C. `displayTransactionHistory()`**
Because `transactionHistory` is `private`, outside code cannot read it directly. This function acts as the safe window to view the records by looping through the list with a `for` loop:

```kotlin
fun displayTransactionHistory() {
    println("Transaction history for $accountHolder:")
    for (transaction in transactionHistory) {
        println(transaction)
    }
}
```

---

### **2. Complete Code**

#### **File: `BankAccount.kt`**
```kotlin
class BankAccount(
    var accountHolder: String,
    var balance: Double
) {
    // Private list to store transaction logs internally
    private val transactionHistory = mutableListOf<String>()

    fun deposit(amount: Double) {
        balance += amount
        transactionHistory.add("$accountHolder deposited $$amount")
    }

    fun withdraw(amount: Double) {
        if (amount <= balance) {
            balance -= amount
            transactionHistory.add("$accountHolder withdrew $$amount")
        } else {
            println("You don't have the funds to withdraw $$amount")
        }
    }

    fun displayTransactionHistory() {
        println("\n--- Transaction history for $accountHolder ---")
        for (transaction in transactionHistory) {
            println(transaction)
        }
    }
}
```

#### **File: `BankMain.kt`**
```kotlin
fun main() {
    // 1. Create a bank account
    val dennisAccount = BankAccount("Dennis Panjuta", 1343.50)

    // 2. Perform transactions
    dennisAccount.deposit(200.0)
    dennisAccount.withdraw(1200.0)
    dennisAccount.deposit(3000.0)
    dennisAccount.deposit(2500.0)
    dennisAccount.withdraw(3333.50)

    // 3. Display the full history
    dennisAccount.displayTransactionHistory()

    // 4. Check the final balance
    println("\n${dennisAccount.accountHolder}'s total balance is: $${dennisAccount.balance}")
}
```

---

### **3. Console Output & The Floating-Point Gotcha**

```text
--- Transaction history for Dennis Panjuta ---
Dennis Panjuta deposited $200.0
Dennis Panjuta withdrew $1200.0
Dennis Panjuta deposited $3000.0
Dennis Panjuta deposited $2500.0
Dennis Panjuta withdrew $3333.5

Dennis Panjuta's total balance is: $2510.0000000000005
```

#### **Why does the balance have `.0000000000005` at the end?**
Computers use binary (base-2) under the hood. Fractional decimal numbers (base-10 like `0.1` or `0.50`) cannot always be represented exactly in binary floating-point (`Double` / `Float`), leading to tiny rounding artifacts. 
*(In production financial apps, specialized types like `BigDecimal` or storing cents as whole `Int`/`Long` are used to prevent this).*

---

### **Key Takeaways**
1. **Operator Assignment (`+=`, `-=`):** Clean shorthand for updating properties (`balance += amount`).
2. **Defensive Programming:** Use `if-else` guards to prevent illegal states (like overdrafting without permission).
3. **Escaping String Templates:** `$$amount` prints a dollar sign immediately followed by the variable's value.
4. **Encapsulation in Action:** The internal `transactionHistory` list is safely updated and printed through member functions without exposing raw list manipulation to `main()`.
