"""LRU cache and event scheduler. Requires Python 3.9 or newer."""

import heapq
from typing import Iterable


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


if __name__ == "__main__":
    cache = LRUCache(2)
    cache.put(1, 10)
    cache.put(2, 20)
    print("get(1):", cache.get(1))  # 10; key 1 becomes most recent.
    cache.put(3, 30)  # Evicts key 2.
    print("get(2) after eviction:", cache.get(2))  # -1

    adjacent = [(9, 10), (10, 11), (11, 12)]
    overlapping = [(9, 12), (10, 11), (11, 13)]
    print("Adjacent events:", can_attend_all(adjacent), min_rooms_required(adjacent))
    print("Overlapping events:", can_attend_all(overlapping), min_rooms_required(overlapping))
