import re
from ..base import BaseRule


def _next_t_numeric(n: int) -> str:
    return f"T{n+1}"


class AliasStyleTNumericRule(BaseRule):
    rule_type = "rewrite"
    order = 9

    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "enable_alias_style_t_numeric", False):
            return tokens

        sql = "".join(tokens)
        pattern = re.compile(r"\b(FROM|JOIN)\s+([A-Za-z_][\w\.]*)(?:\s+AS)?\s+([A-Za-z_][\w]*)?", re.IGNORECASE)

        mappings = {}
        counter = 0

        def _replacer(match):
            nonlocal counter
            kw, table, alias = match.group(1), match.group(2), match.group(3)
            base = alias or table.split(".")[-1]
            if base not in mappings:
                mappings[base] = _next_t_numeric(counter)
                counter += 1
            new_alias = mappings[base]
            return f"{kw} {table} AS {new_alias}"

        new_sql = pattern.sub(_replacer, sql)

        if mappings:
            ref_pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in mappings.keys()) + r")\b(?=\.)")
            new_sql = ref_pattern.sub(lambda m: mappings[m.group(1)], new_sql)

        from ...tokenizer import tokenize
        return tokenize(new_sql)
