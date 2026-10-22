# Data Structures & Systems Design: SE Intern Assignment

Chaitanya Pudota

GitHub repository: https://github.com/Cyril-36/lru-cache-and-event-scheduler

Language: Python 3.9 or newer, standard library only. The full code, with a small demo, is in `solution.py`, and the tests are in `test_solution.py`. Both are in the repository above.

## Assumptions

The brief leaves a few cases open, so these are the choices I made:

- Keys and values are integers. Capacity is set once when the cache is created. A capacity of 0 is allowed and simply stores nothing. A negative capacity raises `ValueError`.
- `get` returns -1 for a missing key, as the brief asks. A stored value of -1 is still allowed, which means the caller can't tell it apart from a miss. I kept the required behaviour anyway.
- Each event is a `(start, end)` pair with `start < end`. The brief doesn't say what `(3, 3)` or `(5, 2)` should mean, so I reject them with `ValueError` instead of guessing.
- An event covers the time from `start` up to, but not including, `end`. A meeting that ends at 10 and one that starts at 10 don't overlap.
- Neither scheduler function changes the list it is given.

## Problem 1: LRU Cache

### My approach

The cache has to do two things quickly. It has to find a key, and it has to know which key was used least recently. No single built-in structure gives me both in O(1), so I combined two.

A dictionary maps each key to a node. That handles lookup without scanning anything.

The nodes live in a doubly linked list, ordered by when they were last used. The node right after `head` is the least recently used, and the node right before `tail` is the most recently used. Whenever a key is read or written, I unlink its node and reattach it just before `tail`. Eviction then means removing the node right after `head`.

It has to be doubly linked because the dictionary hands me a node that could be anywhere in the list. With both `prev` and `next` pointers I can unlink it by changing two links. With a singly linked list I would first have to walk the list to find the node before it, which is O(n) and defeats the purpose.

I also added a dummy node at each end. They are never removed, so every real node always has a neighbour on both sides. That removes the special cases for an empty list and for taking out the first or last item.

How each operation works:

- `get(key)`: look the key up in the dictionary. If it isn't there, return -1 and leave the order alone. If it is, move the node to the end and return its value.
- `put(key, value)`: if the key already exists, update its value and move it to the end. If it's a new key and the cache is full, remove the node after `head` and delete its key from the dictionary, then add the new node at the end.

Each operation is one or two dictionary operations plus a fixed number of pointer changes. Python dictionary operations take expected O(1) time (amortized for inserts, because the table resizes now and then), so `get` and `put` are expected O(1) as well.

```python
class _Node:
    def __init__(self, key: int = 0, value: int = 0):
        self.key = key
        self.value = value
        self.prev = None
        self.next = None


class LRUCache:
    """Integer keys/values; get and put take expected O(1) time.

    Capacity zero is allowed and stores nothing. This class is not thread-safe.
    """

    def __init__(self, capacity: int):
        if type(capacity) is not int:
            raise TypeError("capacity must be an integer")
        if capacity < 0:
            raise ValueError("capacity must not be negative")
        self._capacity = capacity
        self._nodes = {}
        # Sentinels: head <-> least recent ... most recent <-> tail.
        self._head = _Node()
        self._tail = _Node()
        self._head.next = self._tail
        self._tail.prev = self._head

    def _remove(self, node: _Node) -> None:
        node.prev.next = node.next
        node.next.prev = node.prev

    def _append_most_recent(self, node: _Node) -> None:
        previous = self._tail.prev
        previous.next = node
        node.prev = previous
        node.next = self._tail
        self._tail.prev = node

    def _mark_recent(self, node: _Node) -> None:
        self._remove(node)
        self._append_most_recent(node)

    def get(self, key: int) -> int:
        node = self._nodes.get(key)
        if node is None:
            return -1
        self._mark_recent(node)
        return node.value

    def put(self, key: int, value: int) -> None:
        node = self._nodes.get(key)
        if node is not None:
            node.value = value
            self._mark_recent(node)
            return

        if self._capacity == 0:
            return

        if len(self._nodes) == self._capacity:
            oldest = self._head.next
            self._remove(oldest)
            del self._nodes[oldest.key]

        node = _Node(key, value)
        self._nodes[key] = node
        self._append_most_recent(node)
```

### Example

```python
cache = LRUCache(2)
cache.put(1, 10)       # Order: 1
cache.put(2, 20)       # Order: 1, 2
print(cache.get(1))    # 10, order is now 2, 1
cache.put(3, 30)       # Cache is full and 2 is least recent, so 2 is evicted
print(cache.get(2))    # -1
cache.put(1, 100)      # Updates key 1 and makes it most recent
print(cache.get(1))    # 100
```

## Problem 2: Event Scheduler

### can_attend_all

I sort a copy of the events by start time and compare each event with the one before it. If an event starts before the previous one ends, the person can't attend both, so I return `False`. If the start equals the previous end, that's allowed by the adjacency rule.

Comparing neighbours is enough. If every event in the sorted list ends by the time the next one starts, the events run one after another in a single line, so no two of them can overlap.

### min_rooms_required

The way I think about it: the number of rooms needed is the largest number of meetings happening at the same moment.

I go through the meetings in order of start time and keep a min-heap holding the end times of the meetings that are still running. Each entry in the heap is one occupied room. For each new meeting:

1. Pop every end time that is less than or equal to the new start time. Those meetings are over, so their rooms are free again. The "or equal" part is what lets back-to-back meetings share a room.
2. Push the new meeting's end time.
3. The heap size is now the number of meetings running at this start time. I keep the largest size I've seen.

I used a min-heap because the only meeting I ever need to look at is the one that finishes first. The heap shows it in O(1) and removes it in O(log n).

The peak is the correct answer for two reasons. At the moment of the peak, that many meetings really are overlapping, so fewer rooms can't work. And the process only needs a new room when every existing room is busy, so more rooms are never needed. I track the maximum instead of returning the final heap size because the heap usually shrinks again later in the day.

A quick walkthrough with `[(9, 12), (10, 11), (11, 13)]`:

- (9, 12) starts. Nothing to pop. Heap is [12], 1 room in use.
- (10, 11) starts. 12 is still later than 10, so nothing ends. Heap is [11, 12], 2 rooms.
- (11, 13) starts. The meeting ending at 11 is done, so pop it. Push 13. Heap is [12, 13], still 2 rooms.

The answer is 2.

```python
import heapq
from typing import Iterable


Event = tuple[int, int]


def _sorted_events(events: Iterable[Event]) -> list[Event]:
    """Validate positive durations and sort a copy; input is not modified."""
    ordered = list(events)
    for start, end in ordered:
        if start >= end:
            raise ValueError("each event must have start < end")
    ordered.sort(key=lambda event: event[0])
    return ordered


def can_attend_all(events: Iterable[Event]) -> bool:
    ordered = _sorted_events(events)
    for previous, current in zip(ordered, ordered[1:]):
        if current[0] < previous[1]:
            return False
    return True


def min_rooms_required(events: Iterable[Event]) -> int:
    ordered = _sorted_events(events)
    active_end_times = []
    max_rooms = 0

    for start, end in ordered:
        # End times equal to start are free: adjacent meetings can share a room.
        while active_end_times and active_end_times[0] <= start:
            heapq.heappop(active_end_times)
        heapq.heappush(active_end_times, end)
        max_rooms = max(max_rooms, len(active_end_times))

    return max_rooms
```

### Examples

```python
adjacent = [(9, 10), (10, 11), (11, 12)]
print(can_attend_all(adjacent))      # True
print(min_rooms_required(adjacent))  # 1

overlapping = [(9, 12), (10, 11), (11, 13)]
print(can_attend_all(overlapping))      # False
print(min_rooms_required(overlapping))  # 2

print(can_attend_all([]))      # True
print(min_rooms_required([]))  # 0
```

## Final Discussion & Analysis

### Time and space complexity

Here n is the number of events and C is the cache capacity.

| Function | Time | Extra space |
|---|---|---|
| `_Node.__init__` | O(1) | O(1) |
| `_remove`, `_append_most_recent`, `_mark_recent` | O(1) | O(1) |
| `LRUCache.__init__` | O(1) | O(1) |
| `LRUCache.get` | Expected O(1) | O(1) |
| `LRUCache.put` | Expected amortized O(1) | O(1) per call |
| `_sorted_events` | O(n log n) | O(n) |
| `can_attend_all` | O(n log n) | O(n) |
| `min_rooms_required` | O(n log n) | O(n) |

The cache as a whole stores at most C entries, each with a dictionary entry and a list node, so its total memory is O(C).

The O(1) for the cache relies on hashing, and every so often an insert triggers a resize of the dictionary. Resizing costs are amortized across insertions; expected O(1) performance assumes normal hash behaviour. Pathological collisions can still degrade performance.

For the scheduler, sorting costs the most. After sorting, `can_attend_all` makes one O(n) pass. `min_rooms_required` pushes each end time once and pops it at most once, at O(log n) each, so the loop is also O(n log n). The extra space is the sorted copy plus the heap, which never holds more than n entries. Checking that every event has `start < end` takes O(n) and doesn't change these totals.

### Trade-offs: why a hash map and a doubly linked list?

Each structure covers what the other is bad at. A hash map finds a key in O(1), but it has no idea which entry was used least recently. A linked list keeps that order, but finding a key in it means walking the list, which is O(n). Together, the map points straight to the node and the list moves or removes it in O(1).

It has to be a doubly linked list because removing a node from the middle needs access to the node before it. Only a doubly linked list gives me that without searching.

The cost is memory and bookkeeping. Each entry takes a slot in the dictionary plus a node with two pointers, and every operation has to update both structures together or they get out of sync. The simpler alternatives are slower. An array would need elements shifted each time an entry moves, and storing timestamps would mean scanning everything to find the oldest. In real Python code I would probably just use `collections.OrderedDict`, which is built on the same idea, but writing it by hand shows how it works underneath.

### Future proofing: assigning room names

Right now the heap only stores end times, so it knows how many rooms are busy but not which ones. To give each event a named room, I would change three things:

- Store `(end_time, room)` pairs in the active heap instead of just end times.
- Keep a second min-heap of free room numbers.
- Record each event's original index before sorting, so the results come back in the same order the caller passed the events in.

Then for each event, in order of start time, I would first pop every active meeting with `end_time <= start` and put its room back in the free heap. If a free room exists, the event takes the lowest numbered one. If not, I open a new room. Finally I save that room against the event's index and push `(end, room)` onto the active heap.

Room numbers 0, 1, 2 map to "Room A", "Room B", "Room C". For `[(9, 12), (10, 11), (11, 13)]` this gives Room A, Room B, Room B. A new room only opens when every existing room is busy, so it still uses the minimum number of rooms. Time stays O(n log n) and space stays O(n).

### Concurrency: making the LRU cache thread-safe

The problem is that `get` and `put` are each several steps: a dictionary lookup, unlinking a node, relinking it, and sometimes an eviction. If two threads interleave those steps, the list pointers can end up broken, or the dictionary and the list can disagree, for example a key still in the dictionary whose node has already been evicted.

The simplest fix is one `threading.Lock` per cache, held for the whole of every `get` and `put`:

```python
import threading


class LRUCache:
    def __init__(self, capacity: int):
        ...  # same setup as before
        self._lock = threading.Lock()

    def get(self, key: int) -> int:
        with self._lock:
            ...  # same body as before

    def put(self, key: int, value: int) -> None:
        with self._lock:
            ...  # same body as before
```

A few details matter here:

- `get` needs the lock too. It looks like a read, but a hit moves the node to the end of the list, so it changes the cache.
- The private helpers like `_remove` don't take the lock themselves. They only run while `get` or `put` already holds it, and a plain `Lock` would deadlock if they tried to acquire it again.
- The `with` block releases the lock even if an exception is raised.
- Python's GIL isn't enough on its own. It stops two threads running bytecode at the same instant, but a thread can still be paused halfway through `put` while another thread runs.

The downside is that only one thread can use the cache at a time, so under heavy load threads wait in line. If that became a real bottleneck, I would split the keys across several smaller caches, each with its own lock. The catch is that each smaller cache then evicts its own least recently used key, which isn't always the least recently used key overall.
