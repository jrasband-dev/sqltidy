# sqltidy/core.py
from typing import List
from .config import FormatterConfig

class SQLFormatter:
    """Main SQL formatting engine."""

    def __init__(self, config: FormatterConfig = None):
        from .rules.rules import load_rules  # local import avoids circular import
        from .rules.base import FormatterContext
        self.ctx = FormatterContext(config or FormatterConfig())
        self.rules = load_rules()

    def format(self, sql: str) -> str:
        tokens = list(sql)
        for rule in sorted(self.rules, key=lambda r: getattr(r, "order", 100)):
            tokens = rule.apply(tokens, self.ctx)
        return self.join_tokens(tokens)

    def join_tokens(self, tokens: List[str]) -> str:
        output = []
        for t in tokens:
            if t == "\n":
                output.append("\n")
            else:
                if output and not output[-1].endswith("\n") and not output[-1].endswith(" "):
                    output.append(" " + t)
                else:
                    output.append(t)
        return "".join(output).strip()
