from collections import deque
from typing import Deque
import random

from .rules import Rules
from .cards import RANKS, SUITS

class Shoe:
    def __init__(self, rules: Rules, seed: int | None = None):
        self.rules = rules
        self._rng = random.Random(seed)
        self.cards: Deque[str] = deque()
        self.running_count: int = 0
        self._build()

    def _build(self):
        deck = [r+s for r in RANKS for s in SUITS] * self.rules.num_decks
        self._rng.shuffle(deck)
        self.cards = deque(deck)
        self.running_count = 0

    def _need_shuffle(self) -> bool:
        used = self.rules.num_decks*52 - len(self.cards)
        return used / (self.rules.num_decks*52) >= self.rules.penetration

    def deal(self) -> str:
        if not self.cards or self._need_shuffle():
            self._build()
        c = self.cards.popleft()
        self._update_count(c)
        return c

    def _update_count(self, card: str):
        r = card[0]
        if r in "23456": self.running_count += 1
        elif r in "TJQKA": self.running_count -= 1

    def true_count(self) -> float:
        rem = max(0.5, len(self.cards)/52.0)
        return self.running_count / rem