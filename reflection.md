# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
  - The UML design includes three primary classes: `Pet`, `Task`, and `Plan`. `Pet` class represents a pet with care instructions and relevant information about the pet's needs. The `Task` class represents a care task for the pet, including the time required to complete the task and its status. The `Plan` class is a list of tasks the owner needs to complete.
- What classes did you include, and what responsibilities did you assign to each?
  - Pet: represents a pet; should include instructions on how to take care of this pet and any relevant info about the pet's needs
  - Task: represents a task that owner has to do for their pet, should include time needed and task status
  - Plan: a list of tasks the owner has to complete

**b. Design changes**

- Did your design change during implementation?
  - Yes
- If yes, describe at least one change and why you made it.
  - AI had added a few redundant fields like adding time constraints to the Owner class when it was already covered in PlanningConstraints. I decided to remove it to have a cleaner design. 

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
  - A start and end time for the day, blocked windows, priority tasks
- How did you decide which constraints mattered most?
  - I decided time constraints mattered most because the pet's care schedule will depend on owner's available time. 

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
  - It prioritizes tasks that have fixed times first before other tasks.
- Why is that tradeoff reasonable for this scenario?
  - That tradeoff was reasonable for this scenario because the other tasks can be filled in after the main important tasks have been.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
  - planning, refactoring, explaning
- What kinds of prompts or questions were most helpful?
  - I asked it to give a plan outline, reevaluate parts, and explain areas I was confused on. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
  - When optimizing the overlap check in the scheduler, Claude suggested using `bisect.insort` to keep the list of busy time intervals sorted so it could exit the overlap check early. It framed this as a performance improvement, but it didn't sit right with me, so I pushed back on the complexity claim.
- How did you evaluate or verify what the AI suggested?
  - I worked through the Big-O myself. `bisect.insort` finds the insertion point in O(log n), but inserting into a list still has to shift every element after it, which is O(n). Doing that for every fixed task meant the "optimization" was actually O(n) per call, not O(log n), and could end up worse than the original append-then-sort-once approach. Once Claude confirmed that analysis, I proposed keeping a separate list of confirmed fixed tasks (sorted for free, since we only append to it in fixed-time order) and merging it with the pre-sorted blocked windows using `heapq.merge`, which is O(n). We compared all three approaches before I had Claude implement the merge version. I confirmed the fix didn't change behavior by rerunning the existing tests and comparing `main.py`'s output before and after.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
  - Tasks with no `fixed_time` sorting last; `mark_complete` not spawning a new occurrence for a task with no pet or an unsupported recurrence value (e.g. `"monthly"`, which silently does nothing since the check only matches `"daily"`/`"weekly"`); fixed tasks that fall outside the day window or overlap a blocked window or another fixed task; overlapping/unsorted blocked windows still producing correct gaps; and `detect_conflicts` correctly ignoring back-to-back tasks (`end_a == start_b`) while still flagging same-time and multi-way overlaps.
- Why were these tests important?
  - One test caught an actual bug: `mark_complete` had no guard against being called on an already-completed task, so completing a recurring task twice (e.g. a user double-clicking "complete") would spawn two next occurrences instead of one. I fixed it by returning early if `self.completed` is already `True`, and the new test pins that behavior down so it can't silently regress.

**b. Confidence**

- How confident are you that your scheduler works correctly?
  - Fairly confident for the core paths (fixed-time placement, conflict detection, priority-based gap filling), since those are now covered by tests. I'm less confident about compounding edge cases in `build_plan`, like multiple overlapping blocked windows combined with several same-priority flexible tasks competing for leftover space in a gap.
- What edge cases would you test next if you had more time?
  - Boundary conditions on `day_start`/`day_end` (a task ending exactly at `day_end`, a zero-length day), a flexible task whose duration fits the sum of multiple gaps but not any single gap (should still be skipped, not split), and ensure the greedy gap-filling behavior allows a lower-priority shorter task to fill space a higher-priority task couldn't fit into within the same gap.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
  - I'm satisfied with discussions with AI on various tradeoffs and design decisions throughout the project.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
  - I would have initially added Owner to DailyPlan from the start instead of adding Pet to DailyPlan. I initially thought DailyPlan should not be for each pet, but I let AI convince me otherwise based on its limited information.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
  - Systems designed by AI can sometimes be overcomplicated or have oversights, so it's important to review the design to ensure that it is make sense, especially there's rarely one correct way to design a system.
