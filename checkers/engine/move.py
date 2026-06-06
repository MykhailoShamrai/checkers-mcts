"""Move representation.

A :class:`Move` describes a single legal turn. It is general enough to encode
both a simple step and an arbitrarily long capture sequence (mandatory
multi-captures and long flying-king captures).

Encoding
--------
* ``squares`` -- the ordered list of squares the moving piece occupies,
  starting with its origin and ending with its final landing square. A simple
  step has ``len(squares) == 2``; an n-capture has ``n + 1`` entries.
* ``captured`` -- the squares of the opponent pieces removed by this move
  (empty for a non-capturing move). Captured pieces are removed only at the
  end of the full sequence (standard draughts rule: you may not jump the same
  piece twice and captured pieces stay on the board until the jump ends).

The class is frozen/hashable so moves can be used as dictionary keys in the
search trees.
"""

from __future__ import annotations

from dataclasses import dataclass, field


Square = tuple[int, int]


@dataclass(frozen=True)
class Move:
    squares: tuple[Square, ...]
    captured: tuple[Square, ...] = field(default_factory=tuple)

    @property
    def origin(self) -> Square:
        return self.squares[0]

    @property
    def destination(self) -> Square:
        return self.squares[-1]

    @property
    def is_capture(self) -> bool:
        return len(self.captured) > 0

    @property
    def num_captured(self) -> int:
        return len(self.captured)

    def __str__(self) -> str:
        sep = "x" if self.is_capture else "-"
        return sep.join(f"{r}{c}" for r, c in self.squares)