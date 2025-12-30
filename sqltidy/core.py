# sqltidy/core.py
import re
from typing import List
from .config import TidyConfig
from .tokenizer import TOKEN_RE

class SQLFormatter:
    """Main SQL formatting engine."""

    def __init__(self, config: TidyConfig = None):
        from .rules import load_rules
        from .rules.base import FormatterContext
        self.ctx = FormatterContext(config or TidyConfig())
        self.rules = load_rules()

    def tokenize(self, sql: str) -> List[str]:
        """Convert raw SQL into proper tokens without external dependencies."""
        tokens = []
        for groups in TOKEN_RE.findall(sql):
            # Find the first non-empty capturing group
            for t in groups:
                if t == "":
                    continue
                # normalize whitespace
                if t.isspace():
                    if "\n" in t:
                        tokens.append("\n")
                    else:
                        tokens.append(" ")
                else:
                    tokens.append(t)
                break

        return tokens

    def format(self, sql: str) -> str:
        tokens = self.tokenize(sql)

        # Apply your custom rules
        for rule in sorted(self.rules, key=lambda r: getattr(r, "order", 100)):
            tokens = rule.apply(tokens, self.ctx)

        return self.join_tokens(tokens)

    def join_tokens(self, tokens: List[str]) -> str:
        """Reassemble tokens into formatted SQL text."""
        return "".join(tokens).strip()
