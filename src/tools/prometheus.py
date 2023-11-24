import re


def is_valid_prometheus_metric_name(name: str) -> bool:
    """Checks whether a string is a valid Prometheus metric name."""
    pattern = re.compile(r'^[a-zA-Z_:][a-zA-Z0-9_:]*$')
    return bool(pattern.match(name))


def convert_to_prometheus_metric_name(s: str) -> (str, bool):
    """Converts a string into a valid Prometheus metric name by replacing invalid characters with underscores."""
    original_s = s
    s = re.sub(r'[^a-zA-Z0-9_:]', '_', s)
    s = re.sub(r'^[^a-zA-Z_]', '', s)  # Removes non-alphabetic and non-underscore characters at the beginning
    return s, (original_s != s)
