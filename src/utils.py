# utils.py
import re

# Constants for days per month and year for approximate conversions
DAYS_IN_MONTH = 30
DAYS_IN_YEAR = 365

def validate_cryptoperiod_days(days: int) -> None:
    MAX_DAYS = 365 * 100  # Arbitrary business rule, e.g., 100 years
    if days > MAX_DAYS:
        raise ValueError(f"Cryptoperiod days cannot exceed {MAX_DAYS} days")

def parse_cryptoperiod(period_str: str) -> int:
    """
    Converts a cryptoperiod string like '30d', '6m', '1y' into days.

    - 'd' = days
    - 'm' = months (approx 30 days per month)
    - 'y' = years (365 days per year)

    Args:
        period_str (str): A string like '30d', '6m', or '1y'.

    Returns:
        int: The number of days corresponding to the cryptoperiod.

    Raises:
        ValueError: If the format is incorrect or contains unsupported units.
    """
    match = re.match(r"(\d+)([dmy])", period_str.strip().lower())
    if not match:
        raise ValueError(f"Invalid cryptoperiod format: {period_str}")

    value, unit = match.groups()
    value = int(value)

    if unit == 'd':
        return value
    elif unit == 'm':
        return value * DAYS_IN_MONTH
    elif unit == 'y':
        return value * DAYS_IN_YEAR
    else:
        raise ValueError(f"Unsupported time unit '{unit}' in cryptoperiod: {period_str}")

def format_cryptoperiod(days: int) -> str:
    """
    Converts a number of days into a readable cryptoperiod string,
    choosing the largest possible unit.

    Args:
        days (int): The number of days to format.

    Returns:
        str: A formatted cryptoperiod like '6m' or '1y'.
    """
    if days >= DAYS_IN_YEAR and days % DAYS_IN_YEAR == 0:
        return f"{days // DAYS_IN_YEAR}y"
    elif days >= DAYS_IN_MONTH and days % DAYS_IN_MONTH == 0:
        return f"{days // DAYS_IN_MONTH}m"
    else:
        return f"{days}d"
