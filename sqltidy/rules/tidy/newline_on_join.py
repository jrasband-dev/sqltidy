import re
from ..base import BaseRule


class NewlineOnJoinRule(BaseRule):
    """
    Ensures that ON keyword appears on a new line after JOIN clauses.
    
    Example:
        Before:
            LEFT JOIN Table2 ON Table.Id = Table2.ID
        
        After:
            LEFT JOIN Table2
            ON Table.Id = Table2.ID
    
    This rule only applies when newline_on_join is True in the configuration.
    It handles all JOIN types: INNER JOIN, LEFT JOIN, RIGHT JOIN, FULL JOIN, 
    CROSS JOIN, etc.
    """
    rule_type = "tidy"
    order = 25  # After compact whitespace (20), before leading commas (45)
    
    # JOIN type patterns (dialect-agnostic keywords)
    JOIN_PATTERNS = [
        'INNER JOIN',
        'LEFT JOIN', 
        'RIGHT JOIN',
        'FULL JOIN',
        'LEFT OUTER JOIN',
        'RIGHT OUTER JOIN',
        'FULL OUTER JOIN',
        'CROSS JOIN',
        'JOIN',
    ]
    
    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "newline_on_join", False):
            return tokens
        
        sql = "".join(tokens)
        dialect = ctx.config.dialect
        
        # Build a regex pattern that matches:
        # (JOIN_TYPE) (table_name/alias) (ON)
        # We want to ensure ON appears on a new line
        
        # Pattern explanation:
        # - Match JOIN keyword with optional modifiers (INNER, LEFT, etc.)
        # - Capture table name/identifier (allowing schema.table notation)
        # - Match optional alias (AS alias or just alias)
        # - Find ON keyword that should be on a newline
        
        # First normalize JOIN patterns - make sure they're properly spaced
        for join_pattern in sorted(self.JOIN_PATTERNS, key=len, reverse=True):
            # Normalize the JOIN pattern spacing
            pattern = r'\b' + r'\s+'.join(join_pattern.split()) + r'\b'
            replacement = ' '.join(join_pattern.split())
            sql = re.sub(pattern, replacement, sql, flags=re.IGNORECASE)
        
        # Now handle the ON keyword placement
        # Pattern: (JOIN keywords) (whitespace) (table_identifier with optional alias) (whitespace) (ON)
        # We want to replace any whitespace before ON with a newline
        
        pattern = re.compile(
            r'(\b(?:INNER\s+JOIN|LEFT\s+OUTER\s+JOIN|RIGHT\s+OUTER\s+JOIN|FULL\s+OUTER\s+JOIN|'
            r'LEFT\s+JOIN|RIGHT\s+JOIN|FULL\s+JOIN|CROSS\s+JOIN|JOIN)\b)'
            r'(\s+)'  # whitespace after JOIN
            r'([A-Za-z_][\w\.]*)'  # table name (with optional schema)
            r'(?:\s+(?:AS\s+)?([A-Za-z_][\w]*))?'  # optional alias
            r'(\s+)'  # whitespace before ON
            r'(ON)\b',  # ON keyword
            re.IGNORECASE
        )
        
        def _format_join_on(match):
            join_keyword = match.group(1)  # JOIN keyword(s)
            table_name = match.group(3)    # table name
            alias = match.group(4)         # optional alias
            on_keyword = match.group(6)    # ON keyword
            
            # Build the formatted result
            result = join_keyword + ' ' + table_name
            if alias:
                result += ' ' + alias
            
            # Check if ON is already on a new line
            whitespace_before_on = match.group(5)
            if '\n' not in whitespace_before_on:
                # Add newline before ON if not already present
                result += '\n' + on_keyword
            else:
                # Already has newline, preserve it
                result += whitespace_before_on + on_keyword
            
            return result
        
        new_sql = pattern.sub(_format_join_on, sql)
        
        # Re-tokenize the modified SQL
        from ...tokenizer import tokenize
        return tokenize(new_sql)
