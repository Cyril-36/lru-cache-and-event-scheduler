# LRU Cache and Event Scheduler

My solution to the Data Structures & Systems Design assignment for the SE Intern role.

- An LRU cache where `get` and `put` run in expected O(1) time, built from a dictionary and a doubly linked list.
- An event scheduler with `can_attend_all` and `min_rooms_required`, using sorting and a min-heap.

The full write-up, with my reasoning before each piece of code and answers to the discussion questions, is in [Assignment_Solution.md](Assignment_Solution.md).

## Files

- `solution.py`: the cache and scheduler, plus a short demo.
- `test_solution.py`: tests, using only the standard library.
- `Assignment_Solution.md`: the written answers.

## Running it

You need Python 3.9 or newer. Nothing else has to be installed.

```sh
python3 solution.py
python3 -m unittest -v
```

## Tests

There are 12 tests. Besides the normal cases (eviction order, updates, misses, capacity 0 and 1, back-to-back meetings, nested and duplicate meetings, unsorted and empty input, invalid events), two of them check the code against something independent:

- The cache runs 2,400 random operations side by side with Python's `OrderedDict` and checks after every step that both agree and that the linked list is still wired correctly.
- The scheduler is checked against every possible schedule of up to 4 events on a small time range (1,555 schedules), using a brute-force pairwise overlap check and a count of meetings running at each start time.

Chaitanya Pudota
