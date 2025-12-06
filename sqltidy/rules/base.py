from typing import List
from ..config import TidyConfig

class FormatterContext:
    """Holds configuration for the formatting run."""
    def __init__(self, config: TidyConfig):
        self.config = config

class BaseRule:
    """All rules must inherit from this."""
    order = 100
    rule_type = None  # "tidy" or "rewrite"
    def apply(self, tokens: List[str], ctx: FormatterContext) -> List[str]:
        raise NotImplementedError
