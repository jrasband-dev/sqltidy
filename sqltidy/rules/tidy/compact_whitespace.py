from typing import List, Union
from ..base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import Token, TokenGroup, TokenType


class CompactWhitespaceRule(BaseRule):
    """
    Reduce multiple consecutive whitespace tokens to a single space.
    
    This rule compacts consecutive whitespace while preserving newlines.
    It works on Token objects to avoid re-tokenization.
    """
    rule_type = "tidy"
    order = 20
    supports_token_objects = True  # Use Token-based API
    
    config_fields = {
        "compact": ConfigField(
            name="compact",
            default=True,
            description="Use compact formatting (reduce unnecessary whitespace)?",
            field_type=bool
        )
    }
    
    def apply(self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext) -> List[Union[Token, TokenGroup]]:
        """Apply whitespace compaction using Token objects."""
        # Check if compact mode is enabled
        if not getattr(ctx.config, "compact", True):
            return tokens
        
        return self._process_tokens(tokens)
    
    def _process_tokens(self, tokens: List[Union[Token, TokenGroup]]) -> List[Union[Token, TokenGroup]]:
        """Recursively process tokens to compact whitespace."""
        result = []
        prev = None
        
        for token in tokens:
            if isinstance(token, Token):
                # Skip consecutive whitespace tokens
                if token.type == TokenType.WHITESPACE and prev and isinstance(prev, Token) and prev.type == TokenType.WHITESPACE:
                    continue
                
                result.append(token)
                prev = token
                
            elif isinstance(token, TokenGroup):
                # Recursively process group contents
                processed_tokens = self._process_tokens(token.tokens)
                new_group = TokenGroup(token.group_type, processed_tokens, token.name, token.metadata)
                result.append(new_group)
                prev = new_group
            else:
                result.append(token)
                prev = token
        
        return result
