import re


def is_dns_compatible(s: str, exclude_dot: bool = False, max_length: int = 253) -> bool:
    """
    Validates if a string is DNS compatible.

    Parameters:
        s (str): The string to be checked.
        exclude_dot (bool): If True, excludes the dot from being considered as a valid character. Defaults to False.
        max_length (int): The maximum allowable length of the string. Defaults to 253, as per the DNS specification.

    Returns:
        bool: True if the string is DNS compatible, False otherwise.

    Usage examples:
        print(is_dns_compatible("example.com"))  # returns True
        print(is_dns_compatible("example.com", exclude_dot=True))  # returns False
        print(is_dns_compatible("example-com"))  # returns True
        print(is_dns_compatible("example_com"))  # returns False
        print(is_dns_compatible("this-hostname-is-way-too-long-for-our-specific-use-case", max_length=30))  # returns False
    """

    if len(s) > max_length:
        return False

    if exclude_dot:
        return bool(re.match("^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)$", s))
    else:
        return bool(re.match("^(([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*\.)*([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)$", s))
