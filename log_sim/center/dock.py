class Dock:
    """Single dock with index and position awareness."""

    def __init__(self, index):
        self.index = index
        self.occupied = False

    def __repr__(self):
        status = "occupied" if self.occupied else "free"
        return f"Dock({self.index}, {status})"