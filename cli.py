from __future__ import annotations
import argparse
import json
from functools import partial

from .rules import Rules
from .simulate import run
from .bettor import flat_bettor, ramp_bettor


def _parse_payout(payout: str) -> tuple[int,int]:
    if payout in {"3:2", "3/2", "3-2"}:
        return (3,2)
    if payout in {"6:5", "6/5", "6-5"}:
        return (6,5)
    msg = "payout must be '3:2' or '6:5'"
    raise argparse.ArgumentTypeError(msg)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bjx", description="BJX — modular blackjack simulator")
    p.add_argument("--rounds", "-n", type=int, default=20000, help="number of rounds")
    p.add_argument("--bankroll", "-b", type=int, default=2000, help="starting bankroll")
    p.add_argument("--unit", "-u", type=int, default=10, help="base betting unit")
    p.add_argument("--decks", "-d", type=int, default=6, help="number of decks")
    p.add_argument("--h17", action="store_true", help="dealer hits soft 17 (default S17)")
    p.add_argument("--payout", type=_parse_payout, default=(3,2), help="blackjack payout: 3:2 or 6:5")
    p.add_argument("--penetration", type=float, default=0.75, help="shuffle penetration (0..1)")
    p.add_argument("--bettor", choices=["flat","ramp"], default="ramp", help="betting style")
    p.add_argument("--cap-units", type=int, default=8, help="cap units for ramp bettor")
    p.add_argument("--seed", type=int, default=11, help="RNG seed")
    p.add_argument("--json", action="store_true", help="emit JSON output")

    args = p.parse_args(argv)

    rules = Rules(
        num_decks=args.decks,
        dealer_hits_soft_17=args.h17,
        blackjack_pays_num=args.payout[0],
        blackjack_pays_den=args.payout[1],
        penetration=args.penetration,
    )

    if args.bettor == "flat":
        bettor_fn = flat_bettor
    else:
        bettor_fn = partial(ramp_bettor, cap_units=args.cap_units)

    stats = run(
        num_rounds=args.rounds,
        seed=args.seed,
        bankroll=args.bankroll,
        base_unit=args.unit,
        rules=rules,
        bettor_fn=bettor_fn,
    )

    if args.json:
        print(json.dumps(stats, indent=2))
    else:
        print(
            f"Rounds: {stats['rounds']}
"
            f"Hands: {stats['hands']}
"
            f"Final Bankroll: {stats['final_bankroll']}
"
            f"EV / Round: {stats['ev_per_round']}
"
            f"Stdev / Round: {stats['stdev_per_round']}
"
            f"True Count (end): {stats['true_count']}
"
        )

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())