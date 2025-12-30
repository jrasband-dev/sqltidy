import re
from ..base import BaseRule


def _num_to_letters(n: int) -> str:
    """Convert 0-based index to A, B, ..., Z, AA, AB, ..."""
    letters = []
    n += 1  # make it 1-based for easier modulo math
    while n > 0:
        n, rem = divmod(n - 1, 26)
        letters.append(chr(ord("A") + rem))
    return "".join(reversed(letters))


class AliasStyleABCRule(BaseRule):
    rule_type = "rewrite"
    order = 8

    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "enable_alias_style_abc", False):
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
                mappings[base] = _num_to_letters(counter)
                counter += 1
            new_alias = mappings[base]
            return f"{kw} {table} AS {new_alias}"

        new_sql = pattern.sub(_replacer, sql)

        if mappings:
            ref_pattern = re.compile(r"\b(" + "|".join(re.escape(k) for k in mappings.keys()) + r")\b(?=\.)")
            new_sql = ref_pattern.sub(lambda m: mappings[m.group(1)], new_sql)

        from ...tokenizer import tokenize
        return tokenize(new_sql)
