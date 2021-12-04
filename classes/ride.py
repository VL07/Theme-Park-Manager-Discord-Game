class Ride:
    def __init__(self, data: dict) -> None:
        self._data = data

        self.id = data["id"]
        self.name = data["name"]
        self.price = data["price"]
        self.dep = data["dep"]
        self.defaultEntryPrice = data["dep"]
        self.seats = data["seats"]

        self.stats = _Stats(data["stats"])
        self.size = _Size(data["size"])

class _Stats:
    def __init__(self, data: dict) -> None:
        self._data = data

        self.excitement = data["excitement"]
        self.intensity = data["intensity"]
        self.nausea = data["nausea"]

class _Size:
    def __init__(self, data: dict) -> None:
        self._data = data

        self.x = data["x"]
        self.y = data["y"]
        self.total = data["total"]