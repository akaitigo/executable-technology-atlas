class Adapter:
    def __init__(self):
        self.calls = 0
    def add(self, x, y):
        self.calls += 1
        return x + y
