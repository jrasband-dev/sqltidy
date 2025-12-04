from typing import List
from ..config import FormatterConfig

class FormatterContext:
    """Holds configuration for the formatting run."""
    def __init__(self, config: FormatterConfig):
        self.config = config

class BaseRule:
    """All rules must inherit from this."""
    order = 100
    def apply(self, tokens: List[str], ctx: FormatterContext) -> List[str]:
        raise NotImplementedError
