from ..base import BaseRule
from sqltidy.tokenizer import is_keyword


class UppercaseKeywordsRule(BaseRule):
    rule_type = "tidy"
    order = 10
    
    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "uppercase_keywords", False):
            return tokens
        return [t.upper() if is_keyword(t) else t for t in tokens]
