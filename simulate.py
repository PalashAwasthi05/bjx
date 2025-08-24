from statistics import mean, pstdev
from typing import Callable

from .rules import Rules
from .shoe import Shoe
from .game import Game, Seat
from .bettor import flat_bettor, ramp_bettor


def run(
    num_rounds: int = 20000,
    seed: int = 11,
    bankroll: int = 2000,
    base_unit: int = 10,
    rules: Rules | None = None,
    bettor_fn: Callable[[Shoe, int], int] | None = None,
):
    """Run a session and return summary stats.

    bettor_fn: a callable like flat_bettor or a partial of ramp_bettor.
    """
    rules = rules or Rules()
    shoe = Shoe(rules, seed=seed)
    game = Game(rules, shoe, bettor=bettor_fn or ramp_bettor)
    seat = Seat(bankroll=bankroll, base_unit=base_unit)

    deltas = []
    hands = 0
    for _ in range(num_rounds):
        if seat.bankroll < base_unit:
            break
        r = game.round(seat)
        deltas.append(r.delta)
        hands += r.hands_played

    avg = mean(deltas) if deltas else 0.0
    sd = pstdev(deltas) if len(deltas) > 1 else 0.0
    return {
        "rounds": len(deltas),
        "hands": hands,
        "final_bankroll": seat.bankroll,
        "ev_per_round": round(avg, 4),
        "stdev_per_round": round(sd, 2),
        "true_count": round(shoe.true_count(), 2),
    }

if __name__ == "__main__":
    from .rules import Rules
    print(run(rules=Rules()))