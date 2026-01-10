from typing import List, Union

from .base import BaseRule, FormatterContext
from sqltidy.tokenizer import Token, TokenGroup, TokenType


class SQLServerTopFormattingRule(BaseRule):
    """Ensure TOP clause is properly spaced in SQL Server queries."""

    rule_type = "tidy"
    supported_dialects = ["sqlserver"]
    order = 23
    supports_token_objects = True

    def apply(
        self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext
    ) -> List[Union[Token, TokenGroup]]:
        if ctx.config.dialect != "sqlserver":
            return tokens
        return self._process_tokens(tokens)

    def _process_tokens(
        self, tokens: List[Union[Token, TokenGroup]]
    ) -> List[Union[Token, TokenGroup]]:
        result: List[Union[Token, TokenGroup]] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if isinstance(token, TokenGroup):
                processed = self._process_tokens(token.tokens)
                result.append(
                    TokenGroup(token.group_type, processed, token.name, token.metadata)
                )
                i += 1
                continue
            if (
                isinstance(token, Token)
                and token.type == TokenType.KEYWORD
                and token.value.upper() == "TOP"
            ):
                next_token = tokens[i + 1] if i + 1 < len(tokens) else None
                if (
                    next_token
                    and isinstance(next_token, Token)
                    and next_token.type == TokenType.PUNCTUATION
                    and next_token.value == "("
                ):
                    result.append(token)
                    result.append(Token(" ", TokenType.WHITESPACE))
                    i += 1
                    continue
                result.append(token)
                i += 1
                continue
            result.append(token)
            i += 1
        return result


__all__ = ["SQLServerTopFormattingRule"]
