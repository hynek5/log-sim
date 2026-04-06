from typing import Protocol


class ArrivalSource(Protocol):
    """
    Interface for any arrival generator.
    Any class with next_arrival(t_seconds) -> float satisfies this.
    Python equivalent of a Java interface — uses structural typing (duck typing).
    """

    def next_arrival(self, t_seconds: float) -> float:
        ...

