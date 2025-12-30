from ..base import BaseRule


class IndentSelectColumnsRule(BaseRule):
    """
    Add 4 spaces of indentation to each selected column.
    This rule should run after NewlineAfterSelectRule and LeadingCommasRule.
    """
    rule_type = "tidy"
    order = 50

    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "indent_select_columns", False):
            return tokens

        # Work with tokens directly - add 4 spaces after each newline in SELECT...FROM blocks
        out_tokens = []
        i = 0
        in_select = False
        
        while i < len(tokens):
            t = tokens[i]
            
            # Detect SELECT keyword
            if t.upper() == "SELECT":
                in_select = True
                out_tokens.append(t)
                i += 1
                continue
            
            # Detect FROM keyword - end of column list
            if t.upper() == "FROM" and in_select:
                in_select = False
                # Remove trailing spaces before FROM
                while out_tokens and out_tokens[-1] == "    ":
                    out_tokens.pop()
                out_tokens.append(t)
                i += 1
                continue
            
            # If we're in SELECT block and hit a newline, add 4 spaces after it
            if in_select and t == "\n":
                out_tokens.append(t)
                i += 1
                # Add 4 spaces after the newline
                out_tokens.append("    ")
                continue
            
            out_tokens.append(t)
            i += 1
        
        return out_tokens
