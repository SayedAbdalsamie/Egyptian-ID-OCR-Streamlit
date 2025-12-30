import os
from datetime import datetime
from typing import Dict, Iterable


EASTERN_ARABIC_DIGITS: Dict[str, str] = {
    "0": "٠",
    "1": "١",
    "2": "٢",
    "3": "٣",
    "4": "٤",
    "5": "٥",
    "6": "٦",
    "7": "٧",
    "8": "٨",
    "9": "٩",
}

# Reverse mapping: Eastern Arabic to English
EASTERN_TO_ENGLISH: Dict[str, str] = {
    "٠": "0",
    "١": "1",
    "٢": "2",
    "٣": "3",
    "٤": "4",
    "٥": "5",
    "٦": "6",
    "٧": "7",
    "٨": "8",
    "٩": "9",
}


def ensure_directories(dirs: Iterable[str]) -> None:
    for d in dirs:
        os.makedirs(d, exist_ok=True)


def to_eastern_arabic_numerals(text: str) -> str:
    result_chars = []
    for ch in text:
        result_chars.append(EASTERN_ARABIC_DIGITS.get(ch, ch))
    return "".join(result_chars)


def to_english_numerals(text: str) -> str:
    """
    Convert Eastern Arabic numerals to English numerals.
    Used for BD extraction from Num1.
    """
    result_chars = []
    for ch in text:
        result_chars.append(EASTERN_TO_ENGLISH.get(ch, ch))
    return "".join(result_chars)


def derive_birthdate_from_national_id(national_id: str) -> str:
    """
    Derive birth date from Egyptian national ID.

    Structure (14 digits):
    - 1st digit: century (2 -> 1900s, 3 -> 2000s)
    - next 2: year
    - next 2: month
    - next 2: day
    Returns DD/MM/YYYY or empty string if invalid.
    """
    if len(national_id) < 7 or not national_id.isdigit():
        return ""

    century_code = national_id[0]
    year_two = national_id[1:3]
    month_two = national_id[3:5]
    day_two = national_id[5:7]

    if century_code == "2":
        century = 1900
    elif century_code == "3":
        century = 2000
    else:
        return ""

    try:
        year_full = century + int(year_two)
        month = int(month_two)
        day = int(day_two)
        dt = datetime(year_full, month, day)
    except Exception:
        return ""

    return dt.strftime("%d/%m/%Y")

