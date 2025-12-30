import re
from ..base import BaseRule


class SubqueryToCTERule(BaseRule):
    rule_type = "rewrite"
    order = 5
    
    def _find_cte_end(self, sql):
        """Find the end of the CTE block by matching parentheses."""
        # Find WHERE the WITH clause starts
        with_match = re.search(r'\bWITH\s+', sql, flags=re.IGNORECASE)
        if not with_match:
            return None
        
        # Start from after WITH keyword
        pos = with_match.end()
        paren_depth = 0
        in_cte_block = True
        
        while pos < len(sql) and in_cte_block:
            char = sql[pos]
            
            if char == '(':
                paren_depth += 1
            elif char == ')':
                paren_depth -= 1
                # When we close all parens and find a SELECT/INSERT/UPDATE/DELETE, we're done
                if paren_depth == 0:
                    # Look ahead to see if main query starts
                    remaining = sql[pos+1:].lstrip()
                    if re.match(r'(SELECT|INSERT|UPDATE|DELETE)\b', remaining, re.IGNORECASE):
                        return pos + 1
                    # Check for comma indicating another CTE
                    if remaining.startswith(','):
                        # Continue, there's another CTE
                        pos += 1
                        continue
            
            pos += 1
        
        return None

    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "enable_subquery_to_cte", False):
            return tokens

        # Convert tokens back to SQL string
        sql = "".join(tokens)
        
        # Check if SQL already has CTEs
        cte_end_pos = self._find_cte_end(sql)
        if cte_end_pos is not None:
            # Extract existing CTE block and main query
            existing_cte_block = sql[:cte_end_pos].rstrip()
            main_query = sql[cte_end_pos:].lstrip()
        else:
            existing_cte_block = None
            main_query = sql
        
        # Find subqueries only in the main query part (not in existing CTEs)
        # Pattern to match subqueries: (SELECT ...) 
        pattern = r"\(\s*SELECT(.*?)\)"
        matches = re.findall(pattern, main_query, flags=re.IGNORECASE | re.DOTALL)
        if not matches:
            return tokens

        ctes = []
        # Determine starting index for new CTEs
        if existing_cte_block:
            # Count existing CTEs to avoid name conflicts
            existing_cte_count = len(re.findall(r'\w+\s+AS\s*\(', existing_cte_block, flags=re.IGNORECASE))
            i = existing_cte_count + 1
        else:
            i = 1
            
        # Replace subqueries with CTE references
        for subquery in matches:
            ctename = f"cte_{i}"
            cte_sql = f"{ctename} AS (\nSELECT{subquery}\n)"
            ctes.append(cte_sql)
            # Replace in main query only
            main_query = re.sub(
                r"\(\s*SELECT" + re.escape(subquery) + r"\)",
                ctename,
                main_query,
                flags=re.IGNORECASE | re.DOTALL,
                count=1
            )
            i += 1

        # Build final SQL
        if not ctes:
            return tokens
            
        # Build CTE block
        if existing_cte_block:
            # Append new CTEs to existing ones with leading commas
            cte_block = existing_cte_block + "\n"
            cte_block += "".join(["," + c + "\n" for c in ctes])
        else:
            # Create new CTE block
            cte_block = "WITH " + ctes[0] + "\n"
            if len(ctes) > 1:
                cte_block += "".join(["," + c + "\n" for c in ctes[1:]])

        result_sql = cte_block + main_query
        
        # Re-tokenize the modified SQL
        from ...tokenizer import tokenize
        return tokenize(result_sql)
