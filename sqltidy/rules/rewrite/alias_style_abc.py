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
    
    def _extract_cte_scopes(self, sql):
        """Extract CTE scopes and main query, return list of (scope_sql, start_pos, end_pos)."""
        scopes = []
        
        # Check if there's a WITH clause
        with_match = re.search(r'\bWITH\s+', sql, re.IGNORECASE)
        if not with_match:
            # No CTEs, entire SQL is one scope
            return [(sql, 0, len(sql))]
        
        # Track position in the SQL
        pos = with_match.end()
        cte_pattern = re.compile(r'(\w+)\s+AS\s*\(', re.IGNORECASE)
        
        while pos < len(sql):
            cte_match = cte_pattern.search(sql, pos)
            if not cte_match:
                # No more CTEs, rest is main query
                if pos < len(sql):
                    main_query_start = pos
                    scopes.append((sql[main_query_start:], main_query_start, len(sql)))
                break
            
            # Find matching closing parenthesis for this CTE
            paren_start = cte_match.end() - 1
            paren_count = 1
            i = paren_start + 1
            
            while i < len(sql) and paren_count > 0:
                if sql[i] == '(':
                    paren_count += 1
                elif sql[i] == ')':
                    paren_count -= 1
                i += 1
            
            # CTE content is between the opening and closing parens
            cte_start_pos = cte_match.end()
            cte_end_pos = i - 1
            cte_content = sql[cte_start_pos:cte_end_pos]
            scopes.append((cte_content, cte_start_pos, cte_end_pos))
            
            # Skip whitespace and check for comma (next CTE) or main query
            pos = i
            while pos < len(sql) and sql[pos].isspace():
                pos += 1
            
            if pos < len(sql) and sql[pos] == ',':
                # There's another CTE, skip the comma
                pos += 1
            else:
                # Main query starts here
                if pos < len(sql):
                    scopes.append((sql[pos:], pos, len(sql)))
                break
        
        return scopes

    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "enable_alias_style_abc", False):
            return tokens

        sql = "".join(tokens)
        scopes = self._extract_cte_scopes(sql)
        
        # Process each scope independently and rebuild SQL
        result_sql = sql
        offset = 0
        
        for scope_sql, start_pos, end_pos in scopes:
            new_scope_sql = self._apply_to_scope_text(scope_sql)
            
            # Replace this scope in the result
            actual_start = start_pos + offset
            actual_end = end_pos + offset
            result_sql = result_sql[:actual_start] + new_scope_sql + result_sql[actual_end:]
            
            # Update offset for subsequent replacements
            offset += len(new_scope_sql) - len(scope_sql)
        
        from ...tokenizer import tokenize
        return tokenize(result_sql)
    
    def _apply_to_scope_text(self, sql):
        """Apply alias transformation to a single scope of SQL text."""
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

        return new_sql
