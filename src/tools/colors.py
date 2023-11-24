from ansi2html import Ansi2HTMLConverter
from typing import AnyStr


def ansi_to_html(ansi_str: AnyStr) -> AnyStr:
    """
    Converts an ANSI string (including color codes) to HTML.
    """
    if ansi_str is None:
        return None
    converter = Ansi2HTMLConverter(dark_bg=True)
    html = converter.convert(ansi_str, full=True)
    return html
