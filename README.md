# learnAndroidDev

Personal notes and transcripts for learning Android development with **Kotlin**, following
[Danis Panjuta's Android development course](https://www.udemy.com/course/android-12-app-development-from-scratch/)
(Jetpack Compose + XML track).

## Repository structure

```
DanisPanjuta/
├── Day 1 … Day 32/       # Per-day lesson notes (.md), slides (.pdf) and source code
│   ├── Day 1 – Project setup, MainActivity, onCreate
│   ├── Day 2 – Kotlin basics, Rock Paper Scissors
│   ├── Day 3 – Functions, classes & objects, coffee machine app
│   ├── Day 4 – Lists and objects, Bank Account app
│   ├── Day 5 – First app: Unit Converter (Jetpack Compose)
│   ├── Day 6 – Unit Converter pt. 2, state management (remember / mutableStateOf)
│   ├── Day 7 – Shopping List app, LazyColumn, AlertDialog
│   ├── Day 8 – MVVM architecture, ViewModel, inheritance & interfaces
│   ├── Day 9 – JSON, Retrofit, HTTP/REST APIs, coroutines & recipe app
│   ├── Day 10 – Navigation: NavHost, NavController, routes & objects
│   ├── Day 11 – Location: permissions, FusedLocationProviderClient, Geocoder
│   ├── Day 12 – Google Maps + Geocoding integrated into Shopping List app
│   ├── Day 13 – Wishlist app, Scaffold, TopAppBar, FAB, Navigation
│   ├── Day 14 – Room database, @Entity, @Dao, Repository, Flow, Swipe-to-delete
│   ├── Day 15 – Music App Part 1, Drawer, Account & Subscription views
│   ├── Day 16 – Music App Part 2, BottomBar, BottomSheet, title sync
│   ├── Day 17 – Firebase Chat App Part 1, Auth setup
│   ├── Day 18 – Firebase Chat App Part 2, Chatroom lists & messages
│   ├── Day 19 – Introduction (Udemy meta)
│   ├── Day 20 – Getting Ready with Android Studio (XML track intro)
│   ├── Day 21 – Kotlin Fundamentals — If statements
│   ├── Day 22 – More Kotlin fundamentals: OOP, constructors, inheritance, data classes, lambdas
│   ├── Day 23 – Age in Minutes app, DatePickerDialog
│   ├── Day 24 – Calculator app, LinearLayout, click handling
│   ├── Day 25 – Quiz app, Intents, question model & results screen
│   ├── Day 26 – Drawing app, custom View & Canvas, permissions, saving images
│   ├── Day 27 – 7 Minute Workout, timers, TTS, Room history, BMI calculator
│   ├── Day 28 – Happy Places, location & Google Maps, SQLite, swipe to edit/delete
│   ├── Day 29 – Weather app, Retrofit, JSON, FusedLocation, Dexter permissions
│   ├── Day 30 – Trello clone: Firebase Auth, Firestore, Storage, drag & drop, FCM
│   ├── Day 31 – Where to go now: learning, making money, publishing, games
│   └── Day 32 – Thank you & bonus
└── transcripts/          # Full course transcripts, one folder per day/section
    ├── 01–18             # Jetpack Compose track (setup → Firebase chat app)
    ├── 19–32             # Android 12 / XML track (calculator, quiz, drawing app,
    │                     #   7-minute workout, happy places, weather, Trello clone…)
    └── _full-transcript.txt
```

## Topics covered

- Kotlin fundamentals: variables, functions, classes, data classes, lists
- Jetpack Compose: composables, `remember` / `mutableStateOf`, recomposition, Material design
- Architecture: MVVM
- Networking: JSON, Retrofit, HTTP/REST APIs
- Navigation, Room database, Firebase, Google Maps
- Legacy XML UI toolkit (Android 10/12 sections): RecyclerView, custom views, SQLite, Firestore, FCM
