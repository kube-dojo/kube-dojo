"""Family-parallel scheduling helpers."""
from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator

from .models import CalibrationModel, Family

Cell = tuple[str, str, CalibrationModel]


class FamilyParallelScheduler:
    """Max 1 inflight per family. Codex models share the openai queue."""

    def __init__(self, models: Iterable[CalibrationModel]):
        self.family_order: list[Family] = []
        seen: set[Family] = set()
        for model in models:
            if model.family not in seen:
                seen.add(model.family)
                self.family_order.append(model.family)

    def schedule(self, cells: list[Cell]) -> Iterator[Cell]:
        """Yield cells in round-robin family order.

        The caller owns actual concurrency. This stream avoids same-family
        adjacency while any other family still has available cells.
        """
        queues: dict[Family, deque[Cell]] = {}
        order = list(self.family_order)
        seen: set[Family] = set(order)

        for cell in cells:
            family = cell[2].family
            queues.setdefault(family, deque()).append(cell)
            if family not in seen:
                seen.add(family)
                order.append(family)

        while any(queues.values()):
            emitted_this_round = False
            for family in order:
                queue = queues.get(family)
                if not queue:
                    continue
                emitted_this_round = True
                yield queue.popleft()
            if not emitted_this_round:
                break

