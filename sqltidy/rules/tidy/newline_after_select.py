import re
from ..base import BaseRule


class NewlineAfterSelectRule(BaseRule):
    rule_type = "tidy"
    order = 15
    
    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "newline_after_select", False):
            return tokens

        sql = "".join(tokens)

        # Replace each SELECT ... FROM block independently to avoid cross-replacement
        pattern = re.compile(r"SELECT\s+(.*?)\s+FROM", flags=re.IGNORECASE | re.DOTALL)

        def _format_match(m):
            cols = m.group(1)
            col_list = [c.strip() for c in cols.split(",")]
            formatted_cols = "\n" + ",\n".join(col_list) + "\n"
            return "SELECT" + formatted_cols + "FROM"

        new_sql = pattern.sub(_format_match, sql)

        # Re-tokenize the modified SQL
        from ...tokenizer import tokenize
        return tokenize(new_sql)
