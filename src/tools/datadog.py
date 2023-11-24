import re


def is_valid_datadog_tag(tag: str) -> bool:
    """Checks whether a string is a valid Datadog tag."""
    if len(tag) > 200:
        return False
    pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9_\-:/\.]*$')
    return bool(pattern.match(tag))


def convert_to_datadog_tag(s: str) -> (str, bool):
    """Converts a string into a valid Datadog tag by replacing invalid characters with underscores."""
    original_s = s
    s = s.lower()
    s = re.sub(r'[^a-zA-Z0-9_\-:/\.]', '_', s)
    s = re.sub(r'^[^a-zA-Z]', '', s)  # Removes non-alphabetic characters at the beginning
    s = s[:200]  # Truncate to 200 characters
    return s, (original_s != s)
