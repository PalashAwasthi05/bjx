from dataclasses import dataclass
from typing import List, Deque, Callable
from collections import deque

from .rules import Rules
from .shoe import Shoe
from .cards import hand_value, is_blackjack
from .action import Action
from .policy_basic import basic_policy
from .bettor import ramp_bettor

@dataclass(slots=True)
class Seat:
    bankroll: int
    base_unit: int

@dataclass(slots=True)
class Result:
    delta: int
    hands_played: int

class Game:
    def __init__(self, rules: Rules, shoe: Shoe, bettor: Callable[[Shoe, int], int] | None = None):
        self.rules = rules
        self.shoe = shoe
        self.bettor = bettor or ramp_bettor

    def _deal_initial(self) -> tuple[list[str], list[str]]:
        player = [self.shoe.deal(), self.shoe.deal()]
        dealer = [self.shoe.deal(), self.shoe.deal()]
        return player, dealer

    def _settle(self, bet: int, player: List[str], dealer: List[str]) -> int:
        """Return NET delta (profit/loss). Positive = win, negative = loss."""
        if bet == 0:
            return 0
        if is_blackjack(player) and not is_blackjack(dealer):
            return (self.rules.blackjack_pays_num * bet) // self.rules.blackjack_pays_den
        if is_blackjack(dealer) and not is_blackjack(player):
            return -bet
        pt, _ = hand_value(player)
        dt, _ = hand_value(dealer)
        if pt > 21:
            return -bet
        if dt > 21:
            return bet
        if pt > dt:
            return bet
        if pt < dt:
            return -bet
        return 0

    def _dealer_draw(self, dealer: List[str]):
        while True:
            t, soft = hand_value(dealer)
            if t > 21:
                return
            if t > 17:
                return
            if t == 17:
                if self.rules.dealer_hits_soft_17 and soft:
                    dealer.append(self.shoe.deal())
                    continue
                return
            dealer.append(self.shoe.deal())

    def _play_hand(
        self,
        hand: List[str],
        dealer_up: str,
        bet: int,
        can_double: bool,
    ) -> tuple[List[str], int, bool, int]:
        """
        Play a single player hand to completion (or request split).
        Returns (final_hand, final_bet, done, extra_commit), where extra_commit is
        any additional stake committed during play (e.g., DOUBLE adds +bet).
        """
        first = True
        extra_commit = 0
        while True:
            t, _ = hand_value(hand)
            if t > 21:
                return hand, bet, True, extra_commit

            act = basic_policy(hand, dealer_up, self.rules, first)

            if act is Action.SURRENDER:
                return hand, -(bet // 2), True, extra_commit

            if act is Action.SPLIT:
                # signal split request; handled by _resolve_player (affordability checked there)
                return hand, bet, False, extra_commit

            if act is Action.DOUBLE and first and self.rules.double_allowed and can_double:
                hand.append(self.shoe.deal())
                extra_commit += bet  # reserve an additional bet
                return hand, bet * 2, True, extra_commit

            if act is Action.HIT:
                hand.append(self.shoe.deal())
                first = False
                continue

            # STAND or unable to DOUBLE
            return hand, bet, True, extra_commit

    def _resolve_player(
        self,
        original: List[str],
        dealer_up: str,
        init_bet: int,
        available: int,
    ) -> tuple[List[tuple[List[str], int]], int]:
        """
        Resolve player decisions including up to one split. `available` tracks
        funds available to cover additional commitments (double/split). We assume
        the initial wager has already been reserved from `available` upstream.
        Returns (finished_hands, remaining_available).
        """
        queue: Deque[tuple[List[str], int]] = deque([(original, init_bet)])
        finished: List[tuple[List[str], int]] = []
        split_once = False
        avail = available

        while queue:
            hand, bet = queue.popleft()
            can_double = (avail >= bet)
            h, b, done, extra = self._play_hand(hand, dealer_up, bet, can_double)
            avail -= extra  # consume funds reserved by DOUBLE

            if (
                not done
                and self.rules.split_allowed
                and not split_once
                and len(h) == 2
                and h[0][0] == h[1][0]
                and avail >= bet
            ):
                # approve split: consume additional bet
                split_once = True
                avail -= bet
                h1 = [h[0], self.shoe.deal()]
                h2 = [h[1], self.shoe.deal()]
                queue.append((h1, b))
                queue.append((h2, b))
            else:
                # either done, or split not allowed/affordable -> keep as-is
                finished.append((h, b))

        return finished, avail

    def round(self, seat: Seat) -> Result:
        # propose wager up to bankroll using injected bettor
        wager = min(self.bettor(self.shoe, seat.base_unit), seat.bankroll)
        if wager <= 0:
            return Result(0, 0)

        player, dealer = self._deal_initial()

        # Immediate settlement for blackjacks; bankroll adjusted by NET delta only
        if is_blackjack(player) or is_blackjack(dealer):
            delta = self._settle(wager, player, dealer)
            seat.bankroll += delta
            return Result(delta, 1)

        # Track available funds to cover doubles/split beyond the initial wager
        available = seat.bankroll - wager  # reserve initial stake conceptually
        player_hands, available = self._resolve_player(player, dealer[0], wager, available)

        self._dealer_draw(dealer)

        total_delta = 0
        hands_played = 0
        for ph, pb in player_hands:
            d = self._settle(pb, ph, dealer)
            total_delta += d
            hands_played += 1

        # Adjust bankroll by NET delta only
        seat.bankroll += total_delta
        return Result(total_delta, hands_played)
