from ..base import BaseRule


class CompactWhitespaceRule(BaseRule):
    rule_type = "tidy"
    order = 20
    
    def apply(self, tokens, ctx):
        out = []
        prev = None
        for t in tokens:
            if t == " " and prev == " ":
                continue
            out.append(t)
            prev = t
        return out
