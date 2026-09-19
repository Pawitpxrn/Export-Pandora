import re
from datetime import datetime
from typing import Any, Tuple

def clean_cell_text(text: Any) -> str:
    """Clean extra spaces, normalize linebreaks within table cells."""
    if text is None:
        return ""
    s = str(text)
    # Replace multiple spaces / tabs with single space
    s = re.sub(r"[ \t]+", " ", s)
    # Strip leading/trailing whitespaces on each line
    lines = [line.strip() for line in s.splitlines() if line.strip()]
    return "\n".join(lines).strip()

def parse_data_value(val: Any) -> Tuple[Any, str]:
    """
    Attempts to parse a string value into a typed Python object:
    - float / int
    - date / datetime
    - or fallback to cleaned string
    Returns (parsed_value, data_type_tag)
    """
    if val is None or val == "":
        return "", "empty"
    
    if isinstance(val, (int, float)):
        return val, "number"
    if hasattr(val, "strftime"):
        return val, "date"
    
    val_str = str(val).strip()
    
    # Check for accounting negative number like (1,234.56) or (100)
    neg_match = re.match(r"^\(([0-9,]+(\.[0-9]+)?)\)$", val_str)
    if neg_match:
        num_str = neg_match.group(1).replace(",", "")
        try:
            if "." in num_str:
                return -float(num_str), "number"
            return -int(num_str), "number"
        except ValueError:
            pass

    # Standard numbers with commas like 1,234,567.89 or 1234
    num_match = re.match(r"^[-+]?[0-9]{1,3}(,[0-9]{3})*(\.[0-9]+)?$", val_str)
    if num_match:
        try:
            num_clean = val_str.replace(",", "")
            if "." in num_clean:
                return float(num_clean), "number"
            return int(num_clean), "number"
        except ValueError:
            pass

    # Percentage like 15.5% or 7%
    pct_match = re.match(r"^([0-9]+(\.[0-9]+)?)\s*%$", val_str)
    if pct_match:
        try:
            pct_val = float(pct_match.group(1)) / 100.0
            return pct_val, "percentage"
        except ValueError:
            pass

    # Common date formats (YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY)
    date_formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%Y/%m/%d"
    ]
    for fmt in date_formats:
        try:
            dt = datetime.strptime(val_str, fmt)
            # Handle Thai Buddhist year if year > 2400
            if dt.year > 2400:
                dt = dt.replace(year=dt.year - 543)
            return dt.date(), "date"
        except (ValueError, OverflowError):
            pass

    return clean_cell_text(val_str), "string"
