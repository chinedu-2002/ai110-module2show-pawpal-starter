# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

My initial UML design included four classes: **Task**, **Pet**, **Owner**, and **Scheduler**.

- **Task** holds everything about a single activity — description, scheduled time (`HH:MM`), frequency (once/daily/weekly), priority level, duration in minutes, completion status, due date, and which pet it belongs to. It uses Python's `@dataclass` decorator for clean, concise code.
- **Pet** stores the pet's name, species, and age, plus a list of `Task` objects. It can add/remove tasks and filter for pending ones.
- **Owner** manages a list of `Pet` objects and provides a single method (`get_all_tasks()`) that aggregates every task across all pets — this is key for the Scheduler.
- **Scheduler** is the "brain." It takes an `Owner` reference and exposes sorting, filtering, conflict detection, recurring task logic, and daily schedule generation.

The relationships are: an Owner *has many* Pets, a Pet *has many* Tasks, and the Scheduler *manages* an Owner.

**b. Design changes**

Yes. Originally I considered putting sorting/filtering logic directly inside the `Owner` class. During implementation, I moved all algorithmic logic into `Scheduler` instead. This kept `Owner` focused on data management and made `Scheduler` the single place for all "smart" behavior — cleaner separation of concerns and easier to test.

I also added a `pet_name` field to `Task` so the Scheduler could filter tasks by pet without needing to traverse the Owner → Pet → Task hierarchy every time. This denormalization simplified the filtering methods.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers three constraints:
1. **Time** — Tasks are sorted by their `HH:MM` time string, producing a chronological daily schedule.
2. **Priority** — Tasks can be sorted by priority (high → medium → low) so the most important tasks are visible first.
3. **Frequency** — Daily and weekly tasks auto-generate their next occurrence when completed, so the owner never forgets recurring care routines.

I decided time was the most important constraint because a pet care schedule is fundamentally about *when* things happen. Priority is secondary — it helps the owner decide what to focus on when they're short on time.

**b. Tradeoffs**

One key tradeoff: conflict detection only checks for **exact time matches** (e.g., two tasks both at `08:00`), not overlapping durations. A 30-minute walk at `08:00` and a feeding at `08:15` would not be flagged as a conflict even though they overlap.

This tradeoff is reasonable because: (1) it keeps the algorithm simple and understandable, (2) exact-time conflicts are the most common scheduling mistake, and (3) duration-based overlap detection would require converting time strings to datetime objects and doing interval arithmetic — added complexity for a relatively rare edge case in a pet care app.

---

## 3. AI Collaboration

**a. How you used AI**

I used AI (Claude Code) throughout this project as a coding partner:
- **Design brainstorming**: I described the four classes and their relationships, then used AI to generate the Mermaid.js UML diagram and validate that the class responsibilities made sense.
- **Scaffolding**: AI generated the initial dataclass skeletons with proper type hints and `field(default_factory=list)` patterns.
- **Algorithm implementation**: For sorting, I asked how to use a `lambda` key with `sorted()` for `HH:MM` strings. For recurring tasks, I asked about `timedelta` usage.
- **Test generation**: AI drafted the pytest suite covering happy paths and edge cases, which I reviewed and adjusted.
- **Debugging**: When wiring the Streamlit UI, AI helped me understand `st.session_state` persistence.

The most helpful prompts were specific and contextual: "Based on my Scheduler class, how should `detect_conflicts` work without crashing?" produced much better results than vague requests.

**b. Judgment and verification**

AI initially suggested storing all tasks in a flat global list rather than nesting them under Pet objects. I rejected this because it would break the Owner → Pet → Task hierarchy that the UML defined. Keeping tasks on each Pet meant I could easily answer questions like "show me Mochi's tasks" without extra bookkeeping.

I verified this decision by writing the `filter_by_pet()` test — it confirmed that the pet_name-based filtering worked cleanly with the nested structure.

---

## 4. Testing and Verification

**a. What you tested**

The test suite covers 30+ test cases across these behaviors:
- **Task completion**: `mark_complete()` changes status from pending to done.
- **Task addition**: Adding a task to a Pet increases its task count and sets `pet_name`.
- **Sorting correctness**: Tasks added out of order are returned in chronological `HH:MM` order.
- **Recurrence logic**: Completing a daily task creates a new task for tomorrow; weekly creates one for next week; one-time tasks do not recur.
- **Conflict detection**: Same-time tasks are flagged; different-time tasks are not; cross-pet conflicts are detected.
- **Filtering**: Filter by pet name, completion status, and priority all return correct subsets.
- **Edge cases**: Empty schedules, pets with no tasks, removing non-existent pets.

These tests are important because they verify the Scheduler's "brain" works correctly before the UI ever touches the data. A bug in sorting or conflict detection would silently produce wrong schedules.

**b. Confidence**

I'm **4/5 stars** confident the system works correctly. All core scheduling, sorting, filtering, and conflict detection paths are covered by automated tests.

Edge cases I'd test next with more time:
- Duration-based overlap detection (e.g., 30-min task at 08:00 vs. task at 08:15)
- Very large numbers of tasks (performance)
- Invalid time formats (e.g., "25:99") — currently no input validation
- Streamlit UI integration tests (form submission, session state persistence)

---

## 5. Reflection

**a. What went well**

I'm most satisfied with the clean separation between the logic layer (`pawpal_system.py`) and the UI (`app.py`). Building and verifying everything through the CLI demo (`main.py`) first meant the Streamlit integration was straightforward — just importing classes and calling methods. The "CLI-first" workflow caught bugs early.

**b. What you would improve**

If I had another iteration, I would:
1. Add duration-based overlap detection to make conflict warnings smarter.
2. Implement data persistence (save/load to JSON) so tasks survive across app restarts.
3. Add input validation for time formats and prevent duplicate task descriptions.
4. Build a calendar view in Streamlit to visualize the weekly schedule.

**c. Key takeaway**

The most important thing I learned is that **AI is most effective when you give it clear architectural boundaries**. When I asked AI to "build a pet scheduler," the results were generic. But when I said "implement `detect_conflicts()` that returns warning strings for same-time tasks, given my existing Task dataclass," the output was precise and immediately usable. Being the "lead architect" means defining the *what* and *why*, then using AI to accelerate the *how*.
