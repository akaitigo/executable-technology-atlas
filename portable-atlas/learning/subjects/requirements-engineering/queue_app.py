"""Neutral in-memory queue for finite acceptance checks; no service or persistence."""
class QueueApp:
    def __init__(self, capacity=3, inject_overflow_bug=False):
        if type(capacity) is not int or not 1 <= capacity <= 3 or type(inject_overflow_bug) is not bool:
            raise ValueError("capacity 1..3 and boolean bug flag required")
        self.capacity = capacity
        self.inject_overflow_bug = inject_overflow_bug
        self._items = []

    def enqueue(self, value):
        if len(self._items) >= self.capacity and not self.inject_overflow_bug:
            return False
        self._items.append(value)
        return True

    def dequeue(self):
        if not self._items:
            return None
        return self._items.pop(0)

    def snapshot(self):
        return list(self._items)
