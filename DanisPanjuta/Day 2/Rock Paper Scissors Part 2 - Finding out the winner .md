Here is a clear, structured breakdown and explanation of the tutorial on implementing game logic using Kotlin's **`when` expression**.

---

### **1. Overview**
In this lesson, the instructor replaces long `if-else` chains with Kotlin’s **`when` construct**. Furthermore, the game logic is streamlined by using `when` as an **expression** that computes and returns the winner directly into a variable (`val winner = when { ... }`).

---

### **2. Part 1: Replacing `if-else` with a Basic `when` Statement**

In the previous lesson, assigning the computer's choice was done using `if-else if`:
```kotlin
// Old way:
if (randomNumber == 1) computerChoice = "Rock"
else if (randomNumber == 2) computerChoice = "Paper"
else if (randomNumber == 3) computerChoice = "Scissors"
```

Kotlin provides a cleaner, more readable alternative:
```kotlin
// Modern Kotlin way:
when (randomNumber) {
    1 -> computerChoice = "Rock"
    2 -> computerChoice = "Paper"
    3 -> computerChoice = "Scissors"
}
```
* **How it works:** Kotlin checks the value inside the parentheses `(randomNumber)` and executes the branch `->` that matches.

---

### **3. Part 2: Advanced `when` as an Expression (Evaluating the Winner)**

In Kotlin, `when` can return a value directly to a variable. When used without an argument in parentheses (`when { ... }`), each branch acts as a **Boolean condition** (`true` or `false`).

```kotlin
val winner = when {
    playerChoice == computerChoice -> "Tie"
    playerChoice == "Rock" && computerChoice == "Scissors" -> "Player"
    playerChoice == "Paper" && computerChoice == "Rock" -> "Player"
    playerChoice == "Scissors" && computerChoice == "Paper" -> "Player"
    else -> "Computer"
}
```

---

### **4. How the Game Logic is Optimized**

In Rock, Paper, Scissors, there are **$3 \times 3 = 9$ total possible matchups**. Instead of writing 9 separate checks, the logic is condensed into just **3 simple rules**:

```
                              ┌─── Are both choices identical? ───► YES ──► "Tie"
                              │
                              ├─── Did the Player beat the Computer?
[ 9 Possible Matchups ] ──────┤    • Rock vs Scissors
                              │    • Paper vs Rock             ───► YES ──► "Player"
                              │    • Scissors vs Paper
                              │
                              └─── Everything else (Default/else) ────────► "Computer"
```

1. **Rule 1 (The Tie):**
   * `playerChoice == computerChoice -> "Tie"`
   * Covers 3 possibilities: *Rock vs Rock*, *Paper vs Paper*, *Scissors vs Scissors*.

2. **Rule 2 (Player Wins):**
   * Checks the only 3 winning scenarios for the player using equality (`==`) and the logical AND operator (`&&`):
     * Player picks **Rock** AND Computer picks **Scissors**
     * Player picks **Paper** AND Computer picks **Rock**
     * Player picks **Scissors** AND Computer picks **Paper**

3. **Rule 3 (Computer Wins):**
   * `else -> "Computer"`
   * If it wasn't a tie, and the player didn't win, the only remaining possibility is that the **computer won**.

---

### **5. Key Kotlin Operators Explained**

| Operator / Syntax | Meaning | Example |
| :--- | :--- | :--- |
| `==` | **Equality comparison** (checks if two values are the same; returns `true` or `false`). | `playerChoice == "Rock"` |
| `&&` | **Logical AND** (both the left and right conditions must be `true`). | `playerChoice == "Rock" && computerChoice == "Scissors"` |
| `->` | **Arrow operator** in `when` (separates the condition from the result/action). | `1 -> "Rock"` |
| `else` | **Default branch** (executes if none of the above conditions were met). Mandatory when using `when` to assign a variable. | `else -> "Computer"` |

---

### **6. Complete Code Up to This Point**

```kotlin
fun main() {
    var computerChoice = ""
    var playerChoice = ""

    println("Rock, Paper or Scissors? Enter your choice:")
    playerChoice = readln()

    val randomNumber = (1..3).random()

    when (randomNumber) {
        1 -> computerChoice = "Rock"
        2 -> computerChoice = "Paper"
        3 -> computerChoice = "Scissors"
    }

    println("Computer chose: $computerChoice")

    // Determine the winner
    val winner = when {
        playerChoice == computerChoice -> "Tie"
        playerChoice == "Rock" && computerChoice == "Scissors" -> "Player"
        playerChoice == "Paper" && computerChoice == "Rock" -> "Player"
        playerChoice == "Scissors" && computerChoice == "Paper" -> "Player"
        else -> "Computer"
    }
}
```
