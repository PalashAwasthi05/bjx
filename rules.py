from dataclasses import dataclass


@dataclass(slots=True)
class Rules:
    num_decks: int = 6
    dealer_hits_soft_17: bool = False # S17 default
    blackjack_pays_num: int = 3
    blackjack_pays_den: int = 2
    double_allowed: bool = True
    double_after_hit: bool = False # double only as first decision
    surrender_allowed: bool = True
    split_allowed: bool = True
    resplit_aces: bool = False
    penetration: float = 0.75