import re


class Lexems:
    NEWLINE = "\n"
    SPACE = " "
    NOSPACE = ""
    TAB = "\t"
    COMMA = ","
    OPEN_PARENTHESIS = "("
    CLOSING_PARENTHESIS = ")"
    STATEMENT_TERMINATOR = ";"


def add_newlines(text: str, every_n: int = 1) -> str:
    """
    Inserts a newline character after every_n words in the input text.

    Args:
        text (str): The input string to format.
        every_n (int): Number of words after which to insert a newline.

    Returns:
        str: The formatted string with newlines.
    """
    words = text.split()
    lines = [
        Lexems.SPACE.join(words[i : i + every_n]) for i in range(0, len(words), every_n)
    ]
    return Lexems.NEWLINE.join(lines)


def ensure_trailing_newline(text: str) -> str:
    """
    Ensures the input text ends with a single newline.

    Args:
        text (str): The input string.

    Returns:
        str: The string ending with a newline.
    """
    return text.rstrip("\n") + Lexems.NEWLINE


def remove_extra_newlines(text: str) -> str:
    """
    Collapses multiple consecutive newlines into a single newline.

    Args:
        text (str): The input string.

    Returns:
        str: The string with extra newlines removed.
    """
    return re.sub(r"\n+", Lexems.NEWLINE, text)
