"""Run with: python3 -m unittest -v"""

import itertools
import random
import unittest
from collections import OrderedDict

from solution import LRUCache, can_attend_all, min_rooms_required


class LRUCacheTests(unittest.TestCase):
    def test_get_refreshes_recency(self):
        cache = LRUCache(2)
        cache.put(1, 10)
        cache.put(2, 20)
        self.assertEqual(cache.get(1), 10)
        cache.put(3, 30)
        self.assertEqual(cache.get(2), -1)
        self.assertEqual(cache.get(1), 10)
        self.assertEqual(cache.get(3), 30)

    def test_update_refreshes_without_evicting(self):
        cache = LRUCache(2)
        cache.put(1, 10)
        cache.put(2, 20)
        cache.put(1, 100)
        self.assertEqual(cache.get(2), 20)
        cache.put(1, 101)
        cache.put(3, 30)
        self.assertEqual(cache.get(1), 101)
        self.assertEqual(cache.get(2), -1)

    def test_miss_does_not_change_recency(self):
        cache = LRUCache(2)
        cache.put(1, 10)
        cache.put(2, 20)
        self.assertEqual(cache.get(99), -1)
        cache.put(3, 30)
        self.assertEqual(cache.get(1), -1)
        self.assertEqual(cache.get(2), 20)

    def test_capacity_one(self):
        cache = LRUCache(1)
        cache.put(1, 10)
        cache.put(1, 11)
        self.assertEqual(cache.get(1), 11)
        cache.put(2, 20)
        self.assertEqual(cache.get(1), -1)
        self.assertEqual(cache.get(2), 20)

    def test_zero_capacity(self):
        cache = LRUCache(0)
        cache.put(1, 10)
        self.assertEqual(cache.get(1), -1)

    def test_invalid_capacity(self):
        with self.assertRaises(ValueError):
            LRUCache(-1)
        for capacity in (1.5, "2", True):
            with self.subTest(capacity=capacity), self.assertRaises(TypeError):
                LRUCache(capacity)

    def test_zero_and_negative_values(self):
        cache = LRUCache(2)
        cache.put(0, 0)
        cache.put(-2, -1)
        self.assertEqual(cache.get(0), 0)
        self.assertEqual(cache.get(-2), -1)  # A hit still refreshes recency.
        cache.put(3, 30)
        self.assertEqual(cache.get(0), -1)

    def test_randomized_against_ordered_dict(self):
        rng = random.Random(42)
        for capacity in range(6):
            cache = LRUCache(capacity)
            reference = OrderedDict()
            for _ in range(400):
                key = rng.randrange(10)
                if rng.random() < 0.6:
                    value = rng.randrange(-10, 11)
                    cache.put(key, value)
                    if capacity:
                        reference[key] = value
                        reference.move_to_end(key)
                        if len(reference) > capacity:
                            reference.popitem(last=False)
                else:
                    expected = reference.get(key, -1)
                    if key in reference:
                        reference.move_to_end(key)
                    self.assertEqual(cache.get(key), expected)

                # Check order and both link directions, including sentinel links.
                items = []
                previous = cache._head
                node = previous.next
                while node is not cache._tail:
                    self.assertLess(len(items), capacity)
                    self.assertIs(node.prev, previous)
                    self.assertIs(cache._nodes[node.key], node)
                    items.append((node.key, node.value))
                    previous, node = node, node.next
                self.assertIs(cache._tail.prev, previous)
                self.assertEqual(items, list(reference.items()))
                self.assertEqual(set(cache._nodes), set(reference))


class SchedulerTests(unittest.TestCase):
    def test_representative_schedules(self):
        cases = [
            ([], True, 0),
            ([(9, 10)], True, 1),
            ([(9, 10), (10, 11), (11, 12)], True, 1),
            ([(11, 12), (9, 10), (10, 11)], True, 1),
            ([(9, 12), (10, 11), (11, 13)], False, 2),
            ([(0, 10), (1, 9), (2, 8)], False, 3),
            ([(1, 4), (1, 4), (1, 4)], False, 3),
            ([(0, 3), (1, 3), (3, 5), (3, 6)], False, 2),
            ([(0, 3), (0, 2), (0, 1), (10, 11)], False, 3),
            ([(-3, -1), (-1, 2)], True, 1),
        ]
        for events, expected_attendance, expected_rooms in cases:
            with self.subTest(events=events):
                self.assertEqual(can_attend_all(events), expected_attendance)
                self.assertEqual(min_rooms_required(events), expected_rooms)

    def test_input_not_modified(self):
        events = [(11, 12), (9, 10), (10, 11)]
        original = events.copy()
        can_attend_all(events)
        min_rooms_required(events)
        self.assertEqual(events, original)

    def test_invalid_intervals(self):
        for events in ([(3, 3)], [(4, 2)], [(1, 2), (5, 4)]):
            for function in (can_attend_all, min_rooms_required):
                with self.subTest(events=events, function=function.__name__):
                    with self.assertRaises(ValueError):
                        function(events)

    def test_exhaustive_small_schedules(self):
        intervals = list(itertools.combinations(range(4), 2))
        # 1 + 6 + 36 + 216 + 1296 = 1555 schedules, including duplicates.
        for length in range(5):
            for events in itertools.product(intervals, repeat=length):
                expected_attendance = all(
                    a_end <= b_start or b_end <= a_start
                    for (a_start, a_end), (b_start, b_end)
                    in itertools.combinations(events, 2)
                )
                # Independent oracle: count occupancy at each possible start.
                expected_rooms = max(
                    (sum(start <= time < end for start, end in events)
                     for time, _ in events),
                    default=0,
                )
                self.assertEqual(can_attend_all(events), expected_attendance, events)
                self.assertEqual(min_rooms_required(events), expected_rooms, events)


if __name__ == "__main__":
    unittest.main()
