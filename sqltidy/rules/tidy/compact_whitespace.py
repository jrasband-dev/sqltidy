from ..base import BaseRule, ConfigField


class CompactWhitespaceRule(BaseRule):
    rule_type = "tidy"
    order = 20
    
    config_fields = {
        "compact": ConfigField(
            name="compact",
            default=True,
            description="Use compact formatting (reduce unnecessary whitespace)?",
            field_type=bool
        )
    }
    
    def apply(self, tokens, ctx):
        # Check if compact mode is enabled
        if not getattr(ctx.config, "compact", True):
            return tokens
            
        out = []
        prev = None
        for t in tokens:
            if t == " " and prev == " ":
                continue
            out.append(t)
            prev = t
        return out
