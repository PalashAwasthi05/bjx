from .shoe import Shoe

def flat_bettor(shoe: Shoe, base: int) -> int:
    return max(1, base)

#rudimentary sort of linear ramp by true count
def ramp_bettor(shoe: Shoe, base: int, cap_units: int = 8) -> int:
    tc = shoe.true_count()
    units = 1
    if tc >= 1:
        units = min(1 + int(tc), cap_units)
    return max(base * units, base)