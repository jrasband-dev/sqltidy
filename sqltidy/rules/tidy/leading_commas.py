from ..base import BaseRule


class LeadingCommasRule(BaseRule):
    """
    If ctx.config.leading_commas is True → leading commas:
        SELECT
            a
            ,b
            ,c
    If False → trailing commas (default):
        SELECT
            a,
            b,
            c
    """
    rule_type = "tidy"
    order = 45

    def apply(self, tokens, ctx):
        leading = getattr(ctx.config, "leading_commas", False)
        
        if not leading:
            # Default behavior is trailing commas, which is what NewlineAfterSelectRule produces
            return tokens
        
        # For leading commas, we need to move commas after the preceding newline+space
        # to before the next token (on the same line as the previous value, but after newline+indent)
        out_tokens = []
        i = 0
        
        while i < len(tokens):
            t = tokens[i]
            
            # When we hit a comma, look ahead to see if it's followed by newline+space(s)+next_token
            if t == "," and i + 1 < len(tokens):
                # Check if next is space/newline
                if tokens[i + 1] in (" ", "\n"):
                    # Skip the comma for now, we'll add it later
                    i += 1
                    # Collect the whitespace/newline
                    whitespace = []
                    while i < len(tokens) and tokens[i] in (" ", "\n"):
                        whitespace.append(tokens[i])
                        i += 1
                    
                    # Now we're at the next token, insert: newline + "  " + comma + space
                    out_tokens.append("\n")
                    out_tokens.append(",")

                    # Continue without advancing i (we're now at the next real token)
                    continue
            
            out_tokens.append(t)
            i += 1
        
        return out_tokens
