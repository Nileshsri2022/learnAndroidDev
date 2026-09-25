"""
Generate the MkDocs site from the course notes, transcripts and source code.

Design goals:
  * Top tab bar: Home | App projects | Cheat Sheets | Concept Index | Days 1-18 | Days 19-32
  * Bidirectional switching: Every lecture note has a direct banner link to its
    verbatim transcript; every transcript links directly back to its study note.
  * In-page lecture navigation: Next / Previous lecture buttons on every note.
  * Dedicated "Cheat Sheets" hub: Ready-to-copy code snippets covering Kotlin,
    Compose, MVVM, Room, Retrofit, Permissions, and XML.
  * "Concept Index" glossary: A-Z index linking terms to days/lectures.
  * Source projects browser: 17 browsable Android applications.

Produces (in-memory virtual files):
  index.md                      homepage
  apps/index.md                 gallery of all source projects
  cheatsheets/index.md          centralized cheat sheets & quick reference hub
  glossary/index.md             A-Z concept index & terminology glossary
  days/<nn>/index.md            per-day overview (notes / code / slides / transcripts)
  days/<nn>/<slug>.md           one page per lecture note (with transcript switcher & nav)
  days/<nn>/transcript-*.md     one page per raw transcript (with note switcher)
  days/<nn>/code-<project>/     source browser (Apps tab)
  SUMMARY.md                    explicit navigation for literate-nav
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from urllib.parse import quote

import mkdocs_gen_files

ROOT = Path(__file__).resolve().parent.parent          # docs-site/
REPO = ROOT.parent                                     # learnAndroidDev/
SRC = REPO / "DanisPanjuta"
TRANSCRIPTS = SRC / "transcripts"
GITHUB_BASE = "https://github.com/Nileshsri2022/learnAndroidDev/blob/main/"

COMPOSE_DAYS = range(1, 19)      # Day 1-18  -> Jetpack Compose track
XML_DAYS = range(19, 33)         # Day 19-32 -> Android 12 / XML track

NOTE_RE = re.compile(r"^(\d+)\s*[.\-]?\s*(.*)$")
DASHES_RE = re.compile(r"^-{5,}\s*$")
DAY_PREFIX_RE = re.compile(r"^Day\s*\d+\s*[-–]?\s*(.*)$")

JUNK_PARTS = {"__MACOSX", "build", ".gradle", ".idea", "out", ".kotlin", ".git"}

SOURCE_EXTS = {".kt", ".java", ".xml", ".kts", ".gradle", ".properties",
               ".pro", ".toml", ".cfg", ".json"}
GRADLE_NAMES = {"settings.gradle", "settings.gradle.kts",
                "build.gradle", "build.gradle.kts"}
LANG_MAP = {".kt": "kotlin", ".kts": "kotlin", ".java": "java", ".xml": "xml",
            ".gradle": "groovy", ".properties": "properties", ".pro": "properties",
            ".gitignore": "text", ".toml": "toml", ".json": "json", ".cfg": "ini"}
MAX_CODE_BYTES = 200_000

NAV_DAY_MAX = 30        # sidebar label length for day titles
NAV_LECTURE_MAX = 44    # sidebar label length for lecture titles


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s or "page"


def clean_title(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip(" .-–")


def short_title(text: str, maxlen: int = NAV_DAY_MAX) -> str:
    """Shorten a day/lecture title for sidebar use."""
    t = clean_title(text)
    if len(t) <= maxlen:
        return t
    t = re.sub(r"\s*[-–]\s*Android\s*1[02]\s*(Version)?\s*$", "", t).strip(" -–")
    if len(t) <= maxlen:
        return t
    parts = [p.strip() for p in t.split(" - ") if p.strip()]
    if len(parts) > 1:
        if len(parts[0]) <= maxlen:
            return parts[0]
        if len(parts[-1]) <= maxlen:
            return parts[-1]
    cut = t[:maxlen].rsplit(" ", 1)[0]
    return cut + "…"


def first_h1(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return clean_title(line[2:])
    return None


def is_junk(path: Path) -> bool:
    return any(part in JUNK_PARTS for part in path.parts)


def github_url(path: Path) -> str:
    rel = path.relative_to(REPO).as_posix()
    return GITHUB_BASE + quote(rel)


# --------------------------------------------------------------------------
# Discover days & lectures
# --------------------------------------------------------------------------

def day_titles() -> dict[int, str]:
    titles: dict[int, str] = {}
    if not TRANSCRIPTS.is_dir():
        return titles
    for entry in sorted(TRANSCRIPTS.iterdir()):
        m = re.match(r"^(\d+)\s*-\s*(.+)$", entry.name)
        if entry.is_dir() and m:
            rest = m.group(2)
            dm = DAY_PREFIX_RE.match(rest)
            titles[int(m.group(1))] = clean_title(dm.group(1) if dm else rest)
    return titles


def lectures_for_day(day: int) -> list[tuple[int | None, str, Path]]:
    folder = SRC / f"Day {day}"
    if not folder.is_dir():
        return []
    items: list[tuple[int | None, str, Path]] = []
    for path in sorted(folder.glob("*.md")):
        stem = path.stem
        m = NOTE_RE.match(stem)
        num = int(m.group(1)) if m and m.group(1).isdigit() else None
        title = clean_title(m.group(2)) if m else clean_title(stem)
        h1 = first_h1(path.read_text(encoding="utf-8", errors="replace"))
        items.append((num, h1 or title or f"Lecture {num}", path))
    items.sort(key=lambda it: (it[0] is None, it[0] if it[0] is not None else it[1]))
    return items


def transcripts_for_day(day: int) -> list[tuple[str, Path]]:
    folder = TRANSCRIPTS / _transcript_dirname(day)
    if folder is None or not folder.is_dir():
        return []
    return [(p.stem, p) for p in sorted(folder.glob("*.txt"))]


def _transcript_dirname(day: int) -> str | None:
    if not TRANSCRIPTS.is_dir():
        return None
    for entry in TRANSCRIPTS.iterdir():
        m = re.match(r"^(\d+)\s*-", entry.name)
        if entry.is_dir() and m and int(m.group(1)) == day:
            return entry.name
    return None


def transcript_body(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    title, body_start = path.stem, 0
    for i, line in enumerate(lines[:12]):
        if DASHES_RE.match(line.strip()):
            body_start = i + 1
            break
        lm = re.match(r"^Lecture:\s*(.+)$", line)
        if lm:
            title = clean_title(lm.group(1))
    body = "\n".join(lines[body_start:]).strip()
    return title, body


# --------------------------------------------------------------------------
# Source project discovery
# --------------------------------------------------------------------------

class Project:
    def __init__(self, name: str, root: Path, day: int):
        self.name = name
        self.root = root
        self.day = day
        self.files: list[Path] = []
        self.binaries: int = 0

    @property
    def rel_root(self) -> str:
        return self.root.relative_to(REPO).as_posix()


def discover_projects(day: int) -> list[Project]:
    folder = SRC / f"Day {day}"
    if not folder.is_dir():
        return []

    candidates: list[Path] = []
    for path in sorted(folder.rglob("*")):
        if not path.is_dir() or is_junk(path):
            continue
        if any((path / g).is_file() for g in GRADLE_NAMES):
            candidates.append(path)

    roots: list[Path] = []
    for cand in sorted(candidates, key=lambda p: (len(p.parts), str(p))):
        if not any(cand != r and cand.is_relative_to(r) for r in roots):
            roots.append(cand)

    projects: list[Project] = []
    for root in roots:
        proj = Project(root.name, root, day)
        for f in sorted(root.rglob("*")):
            if not f.is_file() or is_junk(f):
                continue
            if f.name in ("gradlew", "gradlew.bat") or "gradle-wrapper" in f.name:
                continue
            if f.name.lower() in ("local.properties", "google-services.json"):
                continue
            if f.suffix.lower() in SOURCE_EXTS or f.name == ".gitignore":
                if f.stat().st_size <= MAX_CODE_BYTES:
                    proj.files.append(f)
            elif f.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg", ".gif",
                                      ".pdf", ".jar", ".ttf"}:
                proj.binaries += 1
        if proj.files:
            projects.append(proj)
    return projects


def lang_breakdown(proj: Project) -> str:
    langs: dict[str, int] = {}
    for f in proj.files:
        ext = f.suffix.lower()
        key = LANG_MAP.get(ext, ext.strip(".") or "other")
        langs[key] = langs.get(key, 0) + 1
    return ", ".join(f"{v} {k}" for k, v in sorted(langs.items(), key=lambda x: -x[1]))


def project_file_page(proj: Project, f: Path) -> str:
    code = f.read_text(encoding="utf-8", errors="replace").rstrip()
    lang = LANG_MAP.get(f.suffix.lower(), "text")
    fence = "````" if "```" in code else "```"
    rel = f.relative_to(proj.root).as_posix()
    return (
        f"# {html.escape(f.name)}\n\n"
        f"`{html.escape(rel)}` · **[{html.escape(proj.name)}](index.md)** · "
        f"[Day {proj.day}](../index.md) · [GitHub]({github_url(f)}){{: .md-button }}\n\n"
        f"{fence}{lang}\n{code}\n{fence}\n"
    )


def project_overview_page(proj: Project,
                          links: list[tuple[str, str]]) -> str:
    out = [
        f"# 📱 {html.escape(proj.name)}",
        "",
        f"Source code for **Day {proj.day}** · {len(proj.files)} files "
        f"({lang_breakdown(proj)}) · [GitHub]({github_url(proj.root)}){{: .md-button }}",
        "",
        "!!! tip \"How to browse\"",
        "    Open a folder below, or press <kbd>Ctrl</kbd>+<kbd>K</kbd> and type a",
        "    class name (e.g. *WishDao*) to jump straight to a file.",
        "",
    ]
    groups: dict[str, list[tuple[str, str]]] = {}
    for rel, href in links:
        parent = str(Path(rel).parent)
        groups.setdefault(parent, []).append((Path(rel).name, href))

    for i, (folder, files) in enumerate(
            sorted(groups.items(), key=lambda kv: (kv[0] != ".", kv[0]))):
        label = "." if folder == "." else folder
        open_attr = " open" if folder == "." else ""
        out += [f"<details{open_attr}><summary>"
                f"📁 <code>{html.escape(label)}</code> — {len(files)} file(s)</summary>",
                ""]
        out += [f"- [`{html.escape(name)}`]({href})" for name, href in files]
        out += ["", "</details>", ""]

    if proj.binaries:
        out += [f"*{proj.binaries} image/media files are not rendered — "
                f"see them [on GitHub]({github_url(proj.root)}).*", ""]
    return "\n".join(out)


def file_tree_links(proj: Project, href: dict[Path, str]) -> list[tuple[str, str]]:
    return [(f.relative_to(proj.root).as_posix(), href[f]) for f in proj.files]


# --------------------------------------------------------------------------
# Matching Notes & Transcripts
# --------------------------------------------------------------------------

def extract_tokens(s: str) -> set[str]:
    s = re.sub(r"^\d+\s*[-–.]\s*", "", s)
    s = re.sub(r"^Day\s*\d+\s*[-–.]\s*", "", s, flags=re.I)
    toks = set(re.findall(r"[a-z0-9]+", s.lower()))
    for stop in ("and", "the", "our", "of", "in", "for", "to", "a", "with", "is", "part", "app"):
        toks.discard(stop)
    return toks


def match_notes_and_transcripts(
    notes: list[tuple[int | None, str, Path, str]],
    transcripts: list[tuple[str, Path, str, str]]
) -> tuple[dict[str, str], dict[str, str]]:
    note_to_trans: dict[str, str] = {}
    trans_to_note: dict[str, str] = {}

    for num, title, n_path, n_slug in notes:
        n_toks = extract_tokens(n_path.stem)
        best_t_slug, best_score = None, 0.0
        for stem, t_path, t_slug, t_title in transcripts:
            if t_slug in trans_to_note:
                continue
            t_toks = extract_tokens(stem) | extract_tokens(t_title)
            inter = len(n_toks & t_toks)
            score = inter / max(len(n_toks), 1)
            if score > best_score:
                best_score = score
                best_t_slug = t_slug
        if best_score >= 0.35 and best_t_slug:
            note_to_trans[n_slug] = best_t_slug
            trans_to_note[best_t_slug] = n_slug

    return note_to_trans, trans_to_note


# --------------------------------------------------------------------------
# Slugs / output helper
# --------------------------------------------------------------------------

page_slugs: set[str] = set()


def unique_slug(base: str) -> str:
    slug, i = base, 2
    while slug in page_slugs:
        slug = f"{base}-{i}"
        i += 1
    page_slugs.add(slug)
    return slug


def write(vpath: str, content: str) -> None:
    with mkdocs_gen_files.open(vpath, "w") as f:
        f.write(content)


# --------------------------------------------------------------------------
# Cheat Sheets Generator
# --------------------------------------------------------------------------

def generate_cheatsheets() -> str:
    return """# ⚡ Android Development — Cheat Sheets & Quick Reference

Quick, copy-pasteable syntax references covering Kotlin language fundamentals, Jetpack Compose UI, MVVM Architecture, Room Database, Retrofit Networking, Location Permissions, and the Compose vs XML Rosetta Stone.

---

=== "Kotlin Language"

    ### Variables & Types
    ```kotlin
    val name = "Denis"       // Immutable (read-only, preferred)
    var counter = 0          // Mutable (can be reassigned)
    val pi: Double = 3.14159 // Explicit type specification
    ```

    ### Null Safety
    ```kotlin
    var nullable: String? = null
    val length = nullable?.length ?: 0         // Elvis operator fallback
    nullable?.let { println("Not null: $it") }  // Scoped execution if non-null
    ```

    ### Control Flow & Expressions
    ```kotlin
    // 'if' is an expression (returns a value)
    val status = if (score >= 50) "Pass" else "Fail"

    // 'when' replaces switch
    val grade = when (score) {
        in 90..100 -> "A"
        in 80..89  -> "B"
        in 70..79  -> "C"
        else       -> "F"
    }
    ```

    ### Data Classes & Collections
    ```kotlin
    data class User(val id: Int, val name: String, val email: String)
    val updated = user.copy(name = "New Name")

    val list = listOf(1, 2, 3)
    val doubled = list.map { it * 2 }
    val evens = list.filter { it % 2 == 0 }
    ```

    ### Coroutines
    ```kotlin
    // Inside ViewModel
    viewModelScope.launch {
        val result = withContext(Dispatchers.IO) {
            repository.fetchData() // Background thread
        }
        _state.value = result     // Main thread update
    }
    ```

=== "Jetpack Compose UI"

    ### State Management
    ```kotlin
    var count by remember { mutableStateOf(0) }
    var text by rememberSaveable { mutableStateOf("") } // Survives config change
    ```

    ### Core Layouts
    ```kotlin
    // Vertical layout
    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("Title")
        Spacer(modifier = Modifier.height(8.dp))
        Button(onClick = { count++ }) { Text("Count: $count") }
    }

    // Horizontal layout
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text("Left")
        Text("Right")
    }

    // Stacked layout
    Box(contentAlignment = Alignment.Center) {
        Image(painterResource(R.drawable.bg), contentDescription = null)
        Text("Overlay Text", color = Color.White)
    }
    ```

    ### LazyColumn (Scrollable List)
    ```kotlin
    LazyColumn(
        modifier = Modifier.fillMaxSize(),
        verticalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        items(itemsList, key = { it.id }) { item ->
            ItemRow(item = item)
        }
    }
    ```

    ### Side Effects
    ```kotlin
    // Trigger action once or when key changes
    LaunchedEffect(userId) {
        viewModel.loadUserProfile(userId)
    }

    // Trigger coroutine from UI button
    val scope = rememberCoroutineScope()
    Button(onClick = { scope.launch { drawerState.open() } }) { Text("Open") }
    ```

=== "Architecture (MVVM)"

    ### Layer Diagram
    ```
    View (Compose / XML) ──> ViewModel ──> Repository ──> Room DB / Retrofit
           ▲                      │
           └──── StateFlow ───────┘
    ```

    ### ViewModel
    ```kotlin
    class MainViewModel(private val repository: MyRepository) : ViewModel() {
        private val _uiState = MutableStateFlow<UiState>(UiState.Loading)
        val uiState: StateFlow<UiState> = _uiState.asStateFlow()

        fun loadData() {
            viewModelScope.launch {
                try {
                    val data = repository.getData()
                    _uiState.value = UiState.Success(data)
                } catch (e: Exception) {
                    _uiState.value = UiState.Error(e.message ?: "Unknown error")
                }
            }
        }
    }
    ```

    ### Consuming in Compose
    ```kotlin
    @Composable
    fun MainScreen(viewModel: MainViewModel = viewModel()) {
        val state by viewModel.uiState.collectAsState()
        when (state) {
            is UiState.Loading -> CircularProgressIndicator()
            is UiState.Success -> ContentList((state as UiState.Success).data)
            is UiState.Error   -> Text("Error: ${(state as UiState.Error).msg}")
        }
    }
    ```

=== "Room Database"

    ### Entity
    ```kotlin
    @Entity(tableName = "wish_table")
    data class Wish(
        @PrimaryKey(autoGenerate = true)
        val id: Long = 0L,
        @ColumnInfo(name = "wish_title")
        val title: String,
        @ColumnInfo(name = "wish_desc")
        val description: String
    )
    ```

    ### DAO (Data Access Object)
    ```kotlin
    @Dao
    interface WishDao {
        @Insert(onConflict = OnConflictStrategy.IGNORE)
        suspend fun addWish(wish: Wish)

        @Update
        suspend fun updateWish(wish: Wish)

        @Delete
        suspend fun deleteWish(wish: Wish)

        @Query("SELECT * FROM wish_table")
        fun getAllWishes(): Flow<List<Wish>>

        @Query("SELECT * FROM wish_table WHERE id = :id")
        fun getWishById(id: Long): Flow<Wish>
    }
    ```

    ### Database Class
    ```kotlin
    @Database(entities = [Wish::class], version = 1, exportSchema = false)
    abstract class WishDatabase : RoomDatabase() {
        abstract fun wishDao(): WishDao
    }
    ```

=== "Networking (Retrofit)"

    ### API Service Interface
    ```kotlin
    interface ApiService {
        @GET("categories.php")
        suspend fun getCategories(): CategoriesResponse

        @GET("recipes/{id}")
        suspend fun getRecipeDetail(@Path("id") id: String): RecipeDetailResponse
    }
    ```

    ### Retrofit Client Instance
    ```kotlin
    object RetrofitClient {
        private const val BASE_URL = "https://www.themealdb.com/api/json/v1/1/"

        val apiService: ApiService by lazy {
            Retrofit.Builder()
                .baseUrl(BASE_URL)
                .addConverterFactory(GsonConverterFactory.create())
                .build()
                .create(ApiService::class.java)
        }
    }
    ```

=== "Permissions & Location"

    ### AndroidManifest.xml
    ```xml
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    ```

    ### Runtime Permission Request (Compose)
    ```kotlin
    val permissionLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.RequestMultiplePermissions()
    ) { permissions ->
        val fineGranted = permissions[Manifest.permission.ACCESS_FINE_LOCATION] ?: false
        val coarseGranted = permissions[Manifest.permission.ACCESS_COARSE_LOCATION] ?: false
        if (fineGranted || coarseGranted) {
            locationUtils.requestLocationUpdates(viewModel)
        } else {
            // Show rationale toast
        }
    }
    ```

=== "Compose vs XML Rosetta Stone"

    | XML Legacy View Element | Jetpack Compose Equivalent | Notes |
    | :--- | :--- | :--- |
    | `<TextView>` | `Text(text = "...")` | Use `sp` for font sizing in both |
    | `<EditText>` | `OutlinedTextField(...)` | Controlled state in Compose |
    | `<Button>` | `Button(onClick = { }) { Text(...) }` | Composable lambda body |
    | `<ImageView>` | `Image(painter = ..., contentDescription = ...)` | Content description required for accessibility |
    | `<LinearLayout android:orientation="vertical">` | `Column { ... }` | Use `Arrangement` & `Alignment` |
    | `<LinearLayout android:orientation="horizontal">` | `Row { ... }` | Use `Arrangement` & `Alignment` |
    | `<FrameLayout>` | `Box { ... }` | Stacks child widgets on top of each other |
    | `<RecyclerView>` | `LazyColumn { items(...) { } }` | No Adapter or ViewHolder boilerplate |
    | `<ScrollView>` | `Modifier.verticalScroll(rememberScrollState())` | Applied to Column or Box |
    | `findViewById<T>(R.id...)` | Direct State Binding | No IDs or lookup required in Compose |
    | `View.GONE` / `View.VISIBLE` | `if (condition) { Composable() }` | Declarative inclusion/exclusion |
"""


# --------------------------------------------------------------------------
# Concept Index & Glossary Generator
# --------------------------------------------------------------------------

def generate_glossary() -> str:
    return """# 📚 Concept Index & Glossary

An alphabetical reference index of Android development concepts covered across the 32 days of the course, with concise definitions, syntax examples, and direct links to the relevant day overviews.

---

### A
- **Activity:** A single, focused window for user interaction in the classic Android View system ([Day 1](../days/01/index.md), [Day 20](../days/20/index.md)).
- **ADB (Android Debug Bridge):** Command-line tool enabling communication between development computers and Android devices ([Day 20](../days/20/index.md)).
- **AlertDialog:** Modal dialog in Jetpack Compose and XML prompting users for confirmation or input ([Day 7](../days/07/index.md), [Day 18](../days/18/index.md)).
- **Alignment:** Positioning items along the cross axis in Compose layouts (`horizontalAlignment` in Column, `verticalAlignment` in Row) ([Day 5](../days/05/index.md)).
- **Arrangement:** Distributing items along the main axis in Compose layouts (`verticalArrangement` in Column, `horizontalArrangement` in Row) ([Day 5](../days/05/index.md)).
- **AVD (Android Virtual Device):** Software emulator simulating real Android hardware on a PC ([Day 1](../days/01/index.md), [Day 20](../days/20/index.md)).

### B
- **Backend as a Service (BaaS):** Cloud service model providing authentication, databases, and push notifications without server management ([Day 17](../days/17/index.md)).
- **BottomBar / BottomNavigation:** Persistent bottom navigation bar switching top-level app destinations ([Day 16](../days/16/index.md)).
- **BottomSheet / ModalBottomSheetLayout:** Slide-up bottom sheet panel for menus or supplementary content ([Day 16](../days/16/index.md)).
- **Box:** Compose layout container stacking children on top of each other ([Day 5](../days/05/index.md)).

### C
- **Canvas:** Low-level 2D graphics drawing surface used for custom rendering ([Day 26](../days/26/index.md)).
- **Card:** Material Design container with elevated surface and rounded corners ([Day 7](../days/07/index.md), [Day 18](../days/18/index.md)).
- **Cloud Firestore:** Scalable real-time NoSQL cloud document database by Google ([Day 17](../days/17/index.md), [Day 18](../days/18/index.md), [Day 30](../days/30/index.md)).
- **Column:** Vertical layout container placing items from top to bottom ([Day 5](../days/05/index.md)).
- **Composable:** A Kotlin function annotated with `@Composable` emitting UI into the layout tree ([Day 5](../days/05/index.md)).
- **ConstraintLayout:** Flexible layout positioning widgets relative to boundaries and sibling anchors ([Day 20](../days/20/index.md), [Day 24](../days/24/index.md)).
- **Context:** Android system object granting access to application resources, databases, and system services ([Day 11](../days/11/index.md)).
- **Coroutines:** Asynchronous programming framework for Kotlin executing non-blocking background tasks cleanly ([Day 9](../days/09/index.md), [Day 14](../days/14/index.md)).

### D
- **DAO (Data Access Object):** Interface declaring database queries, inserts, updates, and deletes in Room Database ([Day 14](../days/14/index.md), [Day 27](../days/27/index.md)).
- **Data Class:** Kotlin class automatically generating `equals()`, `hashCode()`, `toString()`, and `copy()` ([Day 3](../days/03/index.md), [Day 7](../days/07/index.md)).
- **Density-independent Pixels (dp):** Abstract measurement unit scaling across screen densities ($1 \\text{ dp} = 1 \\text{ px}$ at 160 DPI) ([Day 5](../days/05/index.md), [Day 20](../days/20/index.md)).
- **DropdownMenu:** Floating popup menu anchored to a trigger widget ([Day 5](../days/05/index.md), [Day 6](../days/06/index.md)).

### E
- **Elvis Operator (`?:`):** Fallback operator returning the right-hand value if the left-hand operand is null ([Day 2](../days/02/index.md), [Day 22](../days/22/index.md)).
- **Empty Views Activity:** Android Studio project template configuring an Activity linked to an XML layout ([Day 20](../days/20/index.md)).
- **Entity (@Entity):** Annotation marking a Kotlin data class as a SQLite database table in Room ([Day 14](../days/14/index.md)).
- **Expression:** A programming construct that evaluates to and returns a value. In Kotlin, `if` and `when` are expressions ([Day 21](../days/21/index.md)).

### F
- **Firebase Authentication:** Managed cloud identity service handling user accounts, email/passwords, and session security ([Day 17](../days/17/index.md)).
- **Flow / callbackFlow:** Asynchronous data stream in Kotlin emitting multiple sequential values over time ([Day 14](../days/14/index.md), [Day 18](../days/18/index.md)).
- **FusedLocationProviderClient:** Google Play Services API providing optimized device GPS and network location ([Day 11](../days/11/index.md), [Day 28](../days/28/index.md)).

### G
- **Geocoder / Geocoding:** Converting GPS coordinates (latitude/longitude) into human-readable street addresses, or vice-versa ([Day 11](../days/11/index.md), [Day 12](../days/12/index.md)).
- **Google Maps SDK:** Native Android map component rendering interactive vector maps, markers, and camera positions ([Day 12](../days/12/index.md), [Day 28](../days/28/index.md)).
- **Gradle:** Build automation system managing Android dependencies, plugins, and compilation tasks ([Day 1](../days/01/index.md)).

### I
- **Intent:** Messaging object used to request an action from another app component or navigate between Activities ([Day 25](../days/25/index.md)).
- **ItemTouchHelper:** Android utility enabling swipe-to-delete and drag-and-drop reordering gestures ([Day 28](../days/28/index.md), [Day 30](../days/30/index.md)).

### J
- **Jetpack Compose:** Google's modern, declarative UI toolkit for native Android development ([Day 5](../days/05/index.md) through [Day 18](../days/18/index.md)).
- **JSON (JavaScript Object Notation):** Lightweight data interchange format used in web APIs ([Day 9](../days/09/index.md), [Day 29](../days/29/index.md)).

### L
- **LaunchedEffect:** Composable side-effect executing a suspend block within the composition lifecycle ([Day 9](../days/09/index.md), [Day 18](../days/18/index.md)).
- **LazyColumn:** High-performance vertically scrolling list in Compose rendering only visible elements ([Day 7](../days/07/index.md), [Day 18](../days/18/index.md)).
- **LiveData:** Lifecycle-aware observable data holder class from Android Jetpack ([Day 8](../days/08/index.md), [Day 18](../days/18/index.md)).

### M
- **Modifier:** Fluent configuration object defining sizing, padding, background, borders, and gestures in Compose ([Day 5](../days/05/index.md)).
- **mutableStateOf:** Compose observable state container that triggers recomposition when its value changes ([Day 6](../days/06/index.md)).
- **MVVM (Model-View-ViewModel):** Clean architecture pattern decoupling presentation UI from business logic and data persistence ([Day 8](../days/08/index.md)).

### N
- **NavController / NavHost:** Core Jetpack Compose components coordinating screen transitions and navigation backstacks ([Day 10](../days/10/index.md), [Day 13](../days/13/index.md)).
- **Null Safety:** Kotlin compiler feature preventing `NullPointerException` crashes through explicit nullable types (`String?`) ([Day 2](../days/02/index.md), [Day 22](../days/22/index.md)).

### P
- **Parcelable:** High-performance Android IPC serialization format passing complex objects between screens ([Day 10](../days/10/index.md), [Day 28](../days/28/index.md)).

### R
- **Recomposition:** The process where Jetpack Compose re-runs composables whose underlying observed state has mutated ([Day 6](../days/06/index.md)).
- **remember:** Compose keyword caching a calculation or state variable across recompositions ([Day 6](../days/06/index.md)).
- **Repository Pattern:** Architectural pattern creating an abstraction layer between ViewModels and underlying data sources ([Day 14](../days/14/index.md), [Day 18](../days/18/index.md)).
- **Retrofit:** Type-safe HTTP client library by Square for making REST API calls in Android ([Day 9](../days/09/index.md), [Day 29](../days/29/index.md)).
- **Room Database:** Android Jetpack SQLite object-mapping library providing compile-time query verification ([Day 14](../days/14/index.md), [Day 27](../days/27/index.md)).

### S
- **Scaffold:** Standard Material layout structure providing slots for TopAppBar, BottomBar, FloatingActionButton, and Drawers ([Day 13](../days/13/index.md), [Day 15](../days/15/index.md)).
- **Scale-independent Pixels (sp):** Typographic measurement unit scaling with both display density and accessibility preferences ([Day 5](../days/05/index.md), [Day 20](../days/20/index.md)).
- **Sealed Class:** Class hierarchy with a restricted set of subclasses, enabling exhaustive compile-time pattern matching ([Day 10](../days/10/index.md), [Day 17](../days/17/index.md)).
- **StateFlow:** Hot Flow emitting the current and new state updates to collectors ([Day 8](../days/08/index.md)).

### T
- **Toast:** Brief unobtrusive notification popup displayed near the bottom of the screen ([Day 5](../days/05/index.md), [Day 20](../days/20/index.md)).
- **TopAppBar:** Header bar displaying screen titles, navigation icons, and action buttons ([Day 13](../days/13/index.md), [Day 15](../days/15/index.md)).

### V
- **ViewBinding:** Feature that generates a binding class for each XML layout file, replacing `findViewById` safely ([Day 27](../days/27/index.md)).
- **ViewModel:** Jetpack architectural component storing and managing UI-related data across configuration changes ([Day 8](../days/08/index.md)).

### W
- **when:** Kotlin's pattern matching control flow expression replacing switch statements ([Day 2](../days/02/index.md), [Day 21](../days/21/index.md)).
"""


# --------------------------------------------------------------------------
# Main Generation Logic
# --------------------------------------------------------------------------

titles = day_titles()
apps_nav: list[str] = []
tracks_nav: dict[int, list[str]] = {1: [], 2: []}
all_projects: list[tuple[Project, str]] = []
day_rows = {1: [], 2: []}
totals = {"notes": 0, "transcripts": 0, "code": 0}

for day in sorted(titles):
    if day not in COMPOSE_DAYS and day not in XML_DAYS:
        continue
    track = 1 if day in COMPOSE_DAYS else 2
    day_title = titles.get(day, f"Day {day}")
    notes = lectures_for_day(day)
    transcripts = transcripts_for_day(day)
    projects = discover_projects(day)

    nn = f"{day:02d}"
    section = f"days/{nn}"
    page_slugs = set()

    # ---- 1. Projects first (so day_code is available for note headers) ------
    day_code: list[tuple[str, str, int, Path]] = []
    for proj in projects:
        pslug = unique_slug("code-" + slugify(proj.name))
        pdir = f"{section}/{pslug}"
        hrefs: dict[Path, str] = {}
        seen: dict[str, int] = {}
        for f in proj.files:
            rel_slug = slugify(f.relative_to(proj.root).as_posix())[:110] or "file"
            base = rel_slug + ".md"
            if base in seen:
                seen[base] += 1
                base = rel_slug + f"-{seen[base]}.md"
            else:
                seen[base] = 1
            hrefs[f] = base
        for f in proj.files:
            write(f"{pdir}/{hrefs[f]}", project_file_page(proj, f))
        write(f"{pdir}/index.md",
              project_overview_page(proj, file_tree_links(proj, hrefs)))
        href = f"{pslug}/index.md"
        day_code.append((proj.name, href, len(proj.files), proj.root))
        all_projects.append((proj, f"{section}/{href}"))
        totals["code"] += len(proj.files)

    # ---- 2. Prepare slug items for matching --------------------------------
    note_items: list[tuple[int | None, str, Path, str]] = []
    for num, title, path in notes:
        base = f"{num}-{slugify(title)}" if num is not None else slugify(title)
        slug = unique_slug(base)
        note_items.append((num, title, path, slug))

    trans_items: list[tuple[str, Path, str, str]] = []
    for stem, path in transcripts:
        t_title, _ = transcript_body(path)
        slug = unique_slug(slugify(stem))
        trans_items.append((stem, path, f"transcript-{slug}", clean_title(t_title)))

    note_to_trans, trans_to_note = match_notes_and_transcripts(note_items, trans_items)

    # ---- 3. Write lecture note pages ---------------------------------------
    toc: list[tuple[str, str, str]] = []
    for idx, (num, title, path, slug) in enumerate(note_items):
        raw_text = path.read_text(encoding="utf-8", errors="replace")

        # Top badge row
        badge_parts = ['<span class="doc-badge doc-badge-lecture">📖 Study Note</span>']
        if slug in note_to_trans:
            t_slug = note_to_trans[slug]
            badge_parts.append(f'<a href="../{t_slug}/" class="doc-badge doc-switch-link">🗣 Verbatim Transcript</a>')
        if day_code:
            p_name, p_href, _, _ = day_code[0]
            pslug = p_href.split("/")[0]
            badge_parts.append(f'<a href="../{pslug}/" class="doc-badge doc-code-link">📱 Project: {html.escape(p_name)}</a>')
        badge_html = '\n\n<div class="doc-badge-row">\n  ' + "\n  ".join(badge_parts) + "\n</div>\n\n"

        # Insert after first H1
        h1_m = re.search(r"^(#\s+[^\n]+)", raw_text, re.MULTILINE)
        if h1_m:
            pos = h1_m.end()
            note_body = raw_text[:pos] + badge_html + raw_text[pos:]
        else:
            note_body = badge_html + raw_text

        # Bottom in-page navigation (prev / up / next)
        prev_item = note_items[idx - 1] if idx > 0 else None
        next_item = note_items[idx + 1] if idx < len(note_items) - 1 else None

        prev_html = (
            f'<a href="../{prev_item[3]}/" class="doc-nav-prev">← Previous: {html.escape(short_title(prev_item[1], 28))}</a>'
            if prev_item else '<span></span>'
        )
        next_html = (
            f'<a href="../{next_item[3]}/" class="doc-nav-next">Next: {html.escape(short_title(next_item[1], 28))} →</a>'
            if next_item else '<span></span>'
        )
        up_html = f'<a href="../" class="doc-nav-up">Day {day} Overview</a>'
        nav_html = f"\n\n---\n\n<div class=\"doc-nav-row\">\n  {prev_html}\n  {up_html}\n  {next_html}\n</div>\n"

        write(f"{section}/{slug}.md", note_body + nav_html)
        label = f"{num}. {title}" if num is not None else title
        toc.append((label, f"{slug}.md", slug))

    # ---- 4. Write transcript pages -----------------------------------------
    trans_links: list[tuple[str, str]] = []
    for stem, path, t_slug, t_title in trans_items:
        _, body = transcript_body(path)
        t_badges = ['<span class="doc-badge doc-badge-transcript">🗣 Verbatim Transcript</span>']
        if t_slug in trans_to_note:
            n_slug = trans_to_note[t_slug]
            t_badges.append(f'<a href="../{n_slug}/" class="doc-badge doc-switch-link">📖 Structured Study Note & Code</a>')
        t_badges.append(f'<a href="../" class="doc-badge doc-nav-up">Day {day} Overview</a>')
        t_badge_html = '\n\n<div class="doc-badge-row">\n  ' + "\n  ".join(t_badges) + "\n</div>\n\n"

        write(f"{section}/{t_slug}.md",
              f"# {html.escape(t_title)}\n{t_badge_html}"
              f"> 🗣 Raw course transcript — what the instructor said, word for word.\n\n"
              f"{body}\n")
        trans_links.append((clean_title(t_title), f"{t_slug}.md"))

    # ---- 5. Downloads (PDFs, links, images) --------------------------------
    downloads: list[tuple[str, str]] = []
    folder = SRC / f"Day {day}"
    if folder.is_dir():
        for pdf in sorted(folder.glob("*.pdf")):
            downloads.append((f"📄 {pdf.stem.replace('+', ' ')}", github_url(pdf)))
        for link in sorted(folder.glob("link.txt")):
            url = link.read_text(encoding="utf-8", errors="replace").strip()
            if url.startswith("http"):
                downloads.append((f"🔗 {url}", url))
        for img in sorted(folder.glob("*.png")):
            downloads.append((f"🖼 {img.stem.replace('+', ' ')}", github_url(img)))

    # ---- 6. Day overview page ----------------------------------------------
    overview = [f"# Day {day} — {html.escape(day_title)}", ""]
    track_name = "Jetpack Compose track" if track == 1 else "Android 12 / XML track"
    stats = f"**{track_name}** · **{len(notes)} notes**"
    if trans_links:
        stats += f" · **{len(trans_links)} transcripts**"
    if day_code:
        stats += f" · **{len(day_code)} app project(s)**"
    overview += [stats, ""]

    if notes:
        overview += ["## 📖 Lecture notes", ""]
        overview += [f"- [{html.escape(label)}]({link})" for label, link, _ in toc]
        overview.append("")
    if day_code:
        overview += ["## 📱 Source code", ""]
        overview += [f"- **[{html.escape(name)}]({href})** — {n} files · "
                     f"[GitHub]({github_url(root)})"
                     for name, href, n, root in day_code]
        overview.append("")
    if downloads:
        overview += ["## 📄 Slides & links", ""]
        overview += [f"- [{html.escape(t)}]({u})" for t, u in downloads]
        overview.append("")
    if trans_links:
        overview += ["## 🗣 Raw transcripts", ""]
        overview += ["<details><summary>Show the verbatim lecture transcripts "
                     f"({len(trans_links)})</summary>", ""]
        overview += [f"- [{html.escape(t)}]({link})" for t, link in trans_links]
        overview += ["", "</details>", ""]
    overview += ["", f"[← All app projects](../../apps/index.md)" if day_code else "", ""]
    write(f"{section}/index.md", "\n".join(overview))

    # ---- 7. Navigation items -----------------------------------------------
    day_index = f"{section}/index.md"
    nav_day = f"    - [Day {day} · {html.escape(short_title(day_title))}]({day_index})"
    tracks_nav[track].append(nav_day)
    for label, link, _ in toc:
        short = label if len(label) <= NAV_LECTURE_MAX else label[:NAV_LECTURE_MAX].rsplit(" ", 1)[0] + "…"
        tracks_nav[track].append(f"        - [{html.escape(short)}]({section}/{link})")

    totals["notes"] += len(notes)
    totals["transcripts"] += len(trans_links)
    day_rows[track].append(
        f"| [Day {day}]({day_index}) | {html.escape(day_title)} | {len(notes)} | "
        f"{len(projects) or '—'} |"
    )

# --------------------------------------------------------------------------
# Apps gallery (own tab)
# --------------------------------------------------------------------------

gallery = [
    "# 📱 App projects",
    "",
    f"All **{len(all_projects)} source projects** from the course — "
    f"{totals['code']} browsable files. Also searchable with <kbd>Ctrl</kbd>+<kbd>K</kbd>.",
    "",
    "| Project | Day | Files |",
    "| ------- | --- | ----- |",
]
for proj, href in sorted(all_projects, key=lambda x: x[0].day):
    gallery.append(f"| **[{html.escape(proj.name)}](../{href})** | {proj.day} | "
                   f"{len(proj.files)} |")
gallery += [
    "",
    "!!! note",
    "    Images and binary media files are linked to GitHub; Kotlin, XML and Gradle",
    "    source files are fully rendered here with syntax highlighting.",
    "",
]
write("apps/index.md", "\n".join(gallery))

# --------------------------------------------------------------------------
# Write Cheat Sheets & Glossary Pages
# --------------------------------------------------------------------------

write("cheatsheets/index.md", generate_cheatsheets())
write("glossary/index.md", generate_glossary())

# --------------------------------------------------------------------------
# Homepage
# --------------------------------------------------------------------------

home = [
    "# Android Dev Masterclass — Study Notes",
    "",
    "Comprehensive study notes, full course transcripts, browsable app source code, "
    "and quick reference cheat sheets for **Danis Panjuta's Android 14 & Kotlin Masterclass**.",
    "",
    f"- **{len(titles)} days · {totals['notes']} lecture notes · {totals['transcripts']} transcripts"
    f" · {len(all_projects)} app projects ({totals['code']} source files)**",
    "- Search everything instantly with <kbd>Ctrl</kbd>+<kbd>K</kbd> — notes, transcripts, and code.",
    "",
    "| Feature | Description |",
    "| :--- | :--- |",
    "| 📖 **Learn by Day** | Pick a day from the **Days 1–18 (Compose)** or **Days 19–32 (XML)** tab above |",
    "| 🗣 **Transcript Switcher** | Every lecture note features an instant one-click toggle to its verbatim transcript |",
    "| ⚡ **Cheat Sheets** | Centralized syntax reference for Kotlin, Compose, MVVM, Room, and Retrofit |",
    "| 📚 **Concept Index** | Alphabetical A–Z glossary mapping core Android concepts to specific lessons |",
    "| 📱 **Source Code Browser** | Explore 17 real-world Android projects with syntax-highlighted Kotlin & XML |",
    "",
    "## All days at a glance",
    "",
    "### Jetpack Compose track (Days 1–18)",
    "",
    "| Day | Focus | Notes | Apps |",
    "| --- | ----- | ----- | ---- |",
    *day_rows[1],
    "",
    "### Android 12 / XML track (Days 19–32)",
    "",
    "| Day | Focus | Notes | Apps |",
    "| --- | ----- | ----- | ---- |",
    *day_rows[2],
    "",
    "## The two tracks",
    "",
    "- **Days 1–18 (Jetpack Compose):** Kotlin basics, Jetpack Compose, MVVM, Retrofit REST APIs,",
    "  navigation, location, Google Maps, Room Database, and a live Firebase chat app.",
    "- **Days 19–32 (XML View Toolkit):** Kotlin fundamentals, classic View-based apps —",
    "  calculator, quiz, custom canvas drawing, 7-minute workout, Happy Places, weather, and a complete Trello clone.",
    "",
]
write("index.md", "\n".join(home))

# --------------------------------------------------------------------------
# SUMMARY.md — top tabs
# --------------------------------------------------------------------------

summary = [
    "# Table of contents",
    "",
    "- [Home](index.md)",
    "- [📱 App projects](apps/index.md)",
]
for proj, href in sorted(all_projects, key=lambda x: x[0].day):
    summary.append(f"    - [{html.escape(proj.name)} · Day {proj.day}]({href})")

summary.append("- [⚡ Cheat Sheets](cheatsheets/index.md)")
summary.append("- [📚 Concept Index](glossary/index.md)")
summary.append("- Days 1–18 · Compose()")
summary += tracks_nav[1]
summary.append("- Days 19–32 · XML()")
summary += tracks_nav[2]
summary.append("")
write("SUMMARY.md", "\n".join(summary))
