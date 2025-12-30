import re
from ..base import BaseRule


class SubqueryToCTERule(BaseRule):
    rule_type = "rewrite"
    order = 5

    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "enable_subquery_to_cte", False):
            return tokens

        # Convert tokens back to SQL string
        sql = "".join(tokens)
        
        # VERY naive example implementation:
        pattern = r"\(\s*SELECT(.*?)\)"
        matches = re.findall(pattern, sql, flags=re.IGNORECASE | re.DOTALL)
        if not matches:
            return tokens

        ctes = []
        i = 1
        for subquery in matches:
            ctename = f"cte_{i}"
            cte_sql = f"{ctename} AS (\nSELECT{subquery}\n)"
            ctes.append(cte_sql)
            sql = re.sub(
                r"\(\s*SELECT" + re.escape(subquery) + r"\)",
                ctename,
                sql,
                flags=re.IGNORECASE | re.DOTALL,
                count=1
            )
            i += 1

            # Build CTE block with leading commas for subsequent CTEs:
            # WITH cte_1 AS (...)
            # ,cte_2 AS (...)
            if not ctes:
                return tokens
            cte_block = "WITH " + ctes[0] + "\n"
            if len(ctes) > 1:
                cte_block += "".join(["\n," + c for c in ctes[1:]]) + "\n"

        result_sql = cte_block + sql
        
        # Re-tokenize the modified SQL
        from ...tokenizer import tokenize
        return tokenize(result_sql)
