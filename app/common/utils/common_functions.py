from typing import Union
from decimal import Decimal, ROUND_HALF_UP


def round_half_up(value: float, decimal_places: int = 0) -> Union[int, float]:
    value = Decimal(str(value))
    decimals = Decimal(f"1.{'0'*decimal_places}")
    result = value.quantize(decimals, rounding=ROUND_HALF_UP)
    if decimal_places == 0:
        return int(result)
    return float(result)


def float_to_str_with_2_decimals(value: Union[int, float]) -> str:
    return f"{round_half_up(value, 2):0.2f}"


def find_obj_by_id(obj_list: list, obj_id: int, key: str = "id") -> Union[dict, None]:
    for obj in obj_list:
        if obj.get(key) == obj_id:
            return obj
    return None
