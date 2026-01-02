"""
Oracle CONNECT BY Formatting Rule.

This rule only applies to Oracle dialect and formats hierarchical queries
with CONNECT BY clause.
"""

from ..base import BaseRule


class OracleConnectByFormattingRule(BaseRule):
    """
    Format Oracle hierarchical queries (CONNECT BY) with proper indentation.
    
    Examples:
        SELECT employee_id, manager_id, LEVEL
        FROM employees
        START WITH manager_id IS NULL
        CONNECT BY PRIOR employee_id = manager_id
        ORDER SIBLINGS BY last_name;
    
    This rule only applies to Oracle dialect.
    """
    rule_type = "tidy"
    order = 30
    supported_dialects = {'oracle'}  # Only applies to Oracle
    
    def apply(self, tokens, ctx):
        """Format CONNECT BY hierarchical queries."""
        result = []
        i = 0
        
        while i < len(tokens):
            token = tokens[i]
            
            # Look for START WITH
            if token.upper() == 'START' and i + 1 < len(tokens):
                # Skip whitespace
                next_idx = i + 1
                while next_idx < len(tokens) and tokens[next_idx] in (' ', '\n'):
                    next_idx += 1
                
                # Check for WITH
                if next_idx < len(tokens) and tokens[next_idx].upper() == 'WITH':
                    result.append('\n')
                    result.append(token)  # START
                    result.append(' ')
                    result.append(tokens[next_idx])  # WITH
                    i = next_idx + 1
                    continue
            
            # Look for CONNECT BY
            if token.upper() == 'CONNECT' and i + 1 < len(tokens):
                # Skip whitespace
                next_idx = i + 1
                while next_idx < len(tokens) and tokens[next_idx] in (' ', '\n'):
                    next_idx += 1
                
                # Check for BY
                if next_idx < len(tokens) and tokens[next_idx].upper() == 'BY':
                    result.append('\n')
                    result.append(token)  # CONNECT
                    result.append(' ')
                    result.append(tokens[next_idx])  # BY
                    i = next_idx + 1
                    continue
            
            # Look for ORDER SIBLINGS BY
            if token.upper() == 'ORDER' and i + 2 < len(tokens):
                # Skip whitespace
                next_idx = i + 1
                while next_idx < len(tokens) and tokens[next_idx] in (' ', '\n'):
                    next_idx += 1
                
                # Check for SIBLINGS
                if next_idx < len(tokens) and tokens[next_idx].upper() == 'SIBLINGS':
                    siblings_idx = next_idx
                    next_idx += 1
                    while next_idx < len(tokens) and tokens[next_idx] in (' ', '\n'):
                        next_idx += 1
                    
                    # Check for BY
                    if next_idx < len(tokens) and tokens[next_idx].upper() == 'BY':
                        result.append('\n')
                        result.append(token)  # ORDER
                        result.append(' ')
                        result.append(tokens[siblings_idx])  # SIBLINGS
                        result.append(' ')
                        result.append(tokens[next_idx])  # BY
                        i = next_idx + 1
                        continue
            
            result.append(token)
            i += 1
        
        return result
