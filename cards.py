from typing import List, Tuple

RANKS = "23456789TJQKA"
SUITS = "SHDC"

_value_map = {**{r: int(r) for r in "23456789"}, **{k:10 for k in "TJQK"}}

def hand_value(cards: List[str]) -> Tuple[int, bool]:
    total = 0
    aces = 0
    for c in cards:
        r = c[0]
        if r == "A":
            aces += 1
            total += 11
        else:
            total += _value_map.get(r, 0)
    while total > 21 and aces:
        total -= 10
        aces -= 1
    return total, (aces > 0)

def is_blackjack(cards: List[str]) -> bool:
    t, _ = hand_value(cards)
    return len(cards) == 2 and t == 21