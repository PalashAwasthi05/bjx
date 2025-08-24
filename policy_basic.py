from typing import List
from .rules import Rules
from .cards import hand_value
from .action import Action

_pair_split = {
    "AA": True,  # always split Aces
    "88": True,  # always split 8s
}

_hard = {
    5: {k: Action.HIT for k in range(2,12)},
    6: {k: Action.HIT for k in range(2,12)},
    7: {k: Action.HIT for k in range(2,12)},
    8: {k: Action.HIT for k in range(2,12)},
    9: {3: Action.DOUBLE,4: Action.DOUBLE,5: Action.DOUBLE,6: Action.DOUBLE},
    10:{2: Action.DOUBLE,3: Action.DOUBLE,4: Action.DOUBLE,5: Action.DOUBLE,6: Action.DOUBLE,7: Action.DOUBLE,8: Action.DOUBLE,9: Action.DOUBLE},
    11:{k: Action.DOUBLE for k in range(2,12)},
    12:{4: Action.STAND,5: Action.STAND,6: Action.STAND},
}

_soft = {
    13:{4: Action.DOUBLE,5: Action.DOUBLE,6: Action.DOUBLE},
    14:{4: Action.DOUBLE,5: Action.DOUBLE,6: Action.DOUBLE},
    15:{4: Action.DOUBLE,5: Action.DOUBLE,6: Action.DOUBLE},
    16:{4: Action.DOUBLE,5: Action.DOUBLE,6: Action.DOUBLE},
    17:{3: Action.DOUBLE,4: Action.DOUBLE,5: Action.DOUBLE,6: Action.DOUBLE},
    18:{2: Action.STAND,7: Action.STAND,8: Action.STAND,3: Action.DOUBLE,4: Action.DOUBLE,5: Action.DOUBLE,6: Action.DOUBLE},
}


def _up_to_int(up: str) -> int:
    if up == "A": return 11
    if up in "TJQK": return 10
    return int(up)


def basic_policy(player: List[str], dealer_up: str, rules: Rules, first_decision: bool) -> Action:
    pt, soft = hand_value(player)
    upv = _up_to_int(dealer_up[0])

    if rules.surrender_allowed and first_decision and not soft:
        if pt == 16 and upv in (9,10,11):
            return Action.SURRENDER
        if pt == 15 and upv == 10:
            return Action.SURRENDER

    if rules.split_allowed and first_decision and len(player) == 2 and player[0][0] == player[1][0]:
        key = player[0][0]*2
        if _pair_split.get(key, False):
            return Action.SPLIT

    if not soft:
        if pt <= 8:
            return Action.HIT
        if pt in _hard and upv in _hard[pt]:
            return _hard[pt][upv]
        if 13 <= pt <= 16:
            return Action.STAND if upv <= 6 else Action.HIT
        return Action.STAND
    else:
        if pt in _soft and upv in _soft[pt]:
            act = _soft[pt][upv]
            if act == Action.DOUBLE and not (rules.double_allowed and first_decision):
                return Action.HIT
            return act
        if pt <= 17:
            return Action.HIT
        if pt == 18:
            return Action.STAND if upv in (2,7,8) else Action.HIT
        return Action.STAND
