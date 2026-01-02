"""
SQL Server TOP Keyword Formatting Rule.

This rule only applies to SQL Server dialect and formats the TOP keyword
according to T-SQL conventions.
"""

from ..base import BaseRule


class SQLServerTopFormattingRule(BaseRule):
    """
    Format SQL Server TOP keyword with proper spacing.
    
    Examples:
        SELECT TOP 10 * FROM users
        SELECT TOP(100) PERCENT * FROM orders
        SELECT TOP 1 WITH TIES * FROM ranked_items ORDER BY score
    
    This rule only applies to SQL Server dialect.
    """
    rule_type = "tidy"
    order = 25
    supported_dialects = {'sqlserver'}  # Only applies to SQL Server
    
    def apply(self, tokens, ctx):
        """Format TOP keyword with consistent spacing."""
        result = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            # Look for SELECT followed by TOP
            if token.upper() == 'SELECT' and i + 1 < len(tokens):
                result.append(token)
                i += 1
                
                # Skip whitespace and keep track of it
                whitespace_tokens = []
                while i < len(tokens) and tokens[i] in (' ', '\n'):
                    whitespace_tokens.append(tokens[i])
                    i += 1
                
                # Check for TOP keyword
                if i < len(tokens) and tokens[i].upper() == 'TOP':
                    result.append('\n')
                    result.append(tokens[i])  # TOP keyword
                    i += 1
                    
                    # Ensure space after TOP
                    if i < len(tokens) and tokens[i] not in (' ', '\n'):
                        result.append(' ')
                    
                    continue
                else:
                    # No TOP found, restore the whitespace we skipped
                    result.extend(whitespace_tokens)
                    # Don't increment i, continue to process current token normally
                    continue
            
            result.append(token)
            i += 1
        
        return result
