import re
from ..base import BaseRule

class NewlineJoinPatternRule(BaseRule):
    """
    Ensures JOIN keywords appear on a new line with a blank line before them.
    
    Example:
        Before:
            FROM Table1 INNER JOIN Table2 ON Table1.Id = Table2.ID LEFT JOIN Table3 ON Table1.Id = Table3.ID
        
        After:
            FROM Table1
            
            INNER JOIN Table2
            ON Table1.Id = Table2.ID
            
            LEFT JOIN Table3
            ON Table1.Id = Table3.ID
    
    Configuration:
        newline_join_pattern (bool): If True, adds blank line before JOIN keywords
    """
    rule_type = "tidy"
    order = 24  # Before newline_on_join (25)
    
    # JOIN type patterns
    JOIN_KEYWORDS = [
        'INNER JOIN',
        'LEFT OUTER JOIN',
        'RIGHT OUTER JOIN',
        'FULL OUTER JOIN',
        'LEFT JOIN', 
        'RIGHT JOIN',
        'FULL JOIN',
        'CROSS JOIN',
        'CROSS APPLY',
        'OUTER APPLY',
        'JOIN',
    ]
    
    def apply(self, tokens, ctx):
        enabled = getattr(ctx.config, "newline_join_pattern", False)
        
        if not enabled:
            return tokens
        
        sql = "".join(tokens)
        
        # Process each JOIN type (longest first to match multi-word JOINs first)
        for join_keyword in sorted(self.JOIN_KEYWORDS, key=len, reverse=True):
            # Create pattern to match the JOIN with any preceding whitespace
            keyword_pattern = r'\s+'.join(re.escape(word) for word in join_keyword.split())
            
            # Match any whitespace before the JOIN keyword
            # Replace with double newline (blank line) before JOIN
            regex = re.compile(
                r'\s+(' + keyword_pattern + r')',
                re.IGNORECASE
            )
            sql = regex.sub(r'\n\n\1', sql)
        
        return [sql]
    
    def __repr__(self):
        return f"<NewlineJoinPatternRule(order={self.order})>"
