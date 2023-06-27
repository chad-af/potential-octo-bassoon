from datetime import datetime


def extract_order_id(full_id: str) -> str:
    """
    Extracts the order id from a given full id.

    Args:
        full_id (str): The full id, expected to contain the order id as the last element after splitting by '/'.

    Returns:
        str: The extracted order id.
    """
    return full_id.split("/")[-1]


def shopify_date_str_to_datetime(date_str: str) -> datetime:
    """
    Converts a date string from Shopify into a datetime object.

    Args:
        date_str (str): The date string from Shopify, expected to be in the format: "%Y-%m-%dT%H:%M:%SZ".

    Returns:
        datetime: The converted datetime object.
    """
    return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")


def get_amount_from_shopify_price_set(price_set: dict, key: str) -> float:
    """
    Retrieves the amount from a given Shopify price set.

    Args:
        price_set (dict): The price set dictionary from Shopify.
        key (str): The key to look for in the price set.

    Returns:
        float: The amount associated with the given key. If the key or amount is not found, returns 0.
    """
    return float(price_set.get(key, {}).get("shopMoney", {}).get("amount", 0))
