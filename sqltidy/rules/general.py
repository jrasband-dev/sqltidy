import re
from typing import List, Union, Optional, Dict

from ..lexemes.base import Lexemes

from .base import BaseRule, ConfigField, FormatterContext
from sqltidy.tokenizer import (
    Token,
    TokenGroup,
    TokenType,
    GroupType,
    tokenize_with_types,
    SemanticLevel,
)

# Note: constructs are now accessed via ctx.constructs from SQLScript
# from sqltidy.constructs.general import SUBQUERY


class UppercaseKeywordsRule(BaseRule):
    """Convert SQL keywords to uppercase or lowercase based on dialect conventions."""

    rule_type = "tidy"
    order = 10
    supports_token_objects = True

    config_fields = {
        "uppercase_keywords": ConfigField(
            name="uppercase_keywords",
            default=None,
            description="Convert SQL keywords to UPPERCASE (True) or lowercase (False)",
            field_type=Optional[bool],
            dialect_defaults={
                "sqlserver": True,
                "oracle": True,
                "postgresql": False,
                "mysql": False,
                "sqlite": False,
            },
        )
    }

    DIALECT_DEFAULTS = {
        "sqlserver": True,
        "oracle": True,
        "postgresql": False,
        "mysql": False,
        "sqlite": False,
    }

    def _should_uppercase(self, ctx: FormatterContext) -> bool:
        explicit = getattr(ctx.config, "uppercase_keywords", None)
        if explicit is not None:
            return explicit
        return self.DIALECT_DEFAULTS.get(ctx.config.dialect, True)

    def apply(
        self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext
    ) -> List[Union[Token, TokenGroup]]:
        should_uppercase = self._should_uppercase(ctx)
        return self._process_tokens(tokens, should_uppercase)

    def _process_tokens(
        self, tokens: List[Union[Token, TokenGroup]], should_uppercase: bool
    ) -> List[Union[Token, TokenGroup]]:
        result: List[Union[Token, TokenGroup]] = []
        for token in tokens:
            if isinstance(token, Token):
                if token.type == TokenType.KEYWORD:
                    new_value = (
                        token.value.upper() if should_uppercase else token.value.lower()
                    )
                    result.append(Token(new_value, token.type))
                else:
                    result.append(token)
            elif isinstance(token, TokenGroup):
                processed = self._process_tokens(token.tokens, should_uppercase)
                result.append(
                    TokenGroup(token.group_type, processed, token.name, token.metadata)
                )
            else:
                result.append(token)
        return result


class CompactWhitespaceRule(BaseRule):
    """Reduce multiple consecutive whitespace tokens to a single space."""

    rule_type = "tidy"
    order = 20
    supports_token_objects = True

    config_fields = {
        "compact": ConfigField(
            name="compact",
            default=True,
            description="Use compact formatting (reduce unnecessary whitespace)?",
            field_type=bool,
        )
    }

    def apply(
        self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext
    ) -> List[Union[Token, TokenGroup]]:
        if not getattr(ctx.config, "compact", True):
            return tokens
        return self._process_tokens(tokens)

    def _process_tokens(
        self, tokens: List[Union[Token, TokenGroup]]
    ) -> List[Union[Token, TokenGroup]]:
        result: List[Union[Token, TokenGroup]] = []
        prev: Union[Token, TokenGroup, None] = None
        for token in tokens:
            if isinstance(token, Token):
                if (
                    token.type == TokenType.WHITESPACE
                    and isinstance(prev, Token)
                    and prev.type == TokenType.WHITESPACE
                ):
                    continue
                result.append(token)
                prev = token
            elif isinstance(token, TokenGroup):
                processed = self._process_tokens(token.tokens)
                new_group = TokenGroup(
                    token.group_type, processed, token.name, token.metadata
                )
                result.append(new_group)
                prev = new_group
            else:
                result.append(token)
                prev = token
        return result


class NewlineJoinPatternRule(BaseRule):
    """Ensure JOIN keywords appear on a new line with a blank line before them."""

    rule_type = "tidy"
    order = 24
    supports_token_objects = True

    config_fields = {
        "join_newlines": ConfigField(
            name="join_newlines",
            default=True,
            description="Add blank line before JOIN keywords?",
            field_type=bool,
        )
    }

    JOIN_KEYWORDS = {
        "INNER",
        "LEFT",
        "RIGHT",
        "FULL",
        "CROSS",
        "OUTER",
        "JOIN",
        "APPLY",
    }

    def apply(
        self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext
    ) -> List[Union[Token, TokenGroup]]:
        if not getattr(
            ctx.config, "join_newlines", self.config_fields["join_newlines"].default
        ):
            return tokens
        return self._process_tokens(tokens, first_table_after_from=False)

    def _process_tokens(
        self,
        tokens: List[Union[Token, TokenGroup]],
        first_table_after_from: bool = False,
    ) -> List[Union[Token, TokenGroup]]:
        result: List[Union[Token, TokenGroup]] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if isinstance(token, TokenGroup):
                processed = self._process_tokens(token.tokens, first_table_after_from)
                result.append(
                    TokenGroup(token.group_type, processed, token.name, token.metadata)
                )
                i += 1
                continue
            if isinstance(token, Token):
                if token.type == TokenType.KEYWORD and token.value.upper() == "FROM":
                    first_table_after_from = True
                    result.append(token)
                    i += 1
                    continue
                if token.type == TokenType.KEYWORD and token.value.upper() == "JOIN":
                    if not first_table_after_from:
                        while (
                            result
                            and isinstance(result[-1], Token)
                            and result[-1].type
                            in (TokenType.WHITESPACE, TokenType.NEWLINE)
                        ):
                            result.pop()
                        if (
                            result
                            and isinstance(result[-1], Token)
                            and result[-1].type == TokenType.KEYWORD
                        ):
                            last_keyword = result[-1].value.upper()
                            if last_keyword in (
                                "INNER",
                                "LEFT",
                                "RIGHT",
                                "FULL",
                                "CROSS",
                                "OUTER",
                            ):
                                modifiers = [result.pop()]
                                while (
                                    result
                                    and isinstance(result[-1], Token)
                                    and result[-1].type
                                    in (TokenType.WHITESPACE, TokenType.NEWLINE)
                                ):
                                    result.pop()
                                if (
                                    result
                                    and isinstance(result[-1], Token)
                                    and result[-1].type == TokenType.KEYWORD
                                ):
                                    second_keyword = result[-1].value.upper()
                                    if second_keyword in (
                                        "LEFT",
                                        "RIGHT",
                                        "FULL",
                                        "OUTER",
                                    ):
                                        modifiers.insert(0, result.pop())
                                        while (
                                            result
                                            and isinstance(result[-1], Token)
                                            and result[-1].type
                                            in (TokenType.WHITESPACE, TokenType.NEWLINE)
                                        ):
                                            result.pop()
                                result.append(Token(Lexemes.NEWLINE, TokenType.NEWLINE))
                                result.append(Token(Lexemes.NEWLINE, TokenType.NEWLINE))
                                for mod in modifiers:
                                    result.append(mod)
                                    result.append(Token(" ", TokenType.WHITESPACE))
                        else:
                            result.append(Token(Lexemes.NEWLINE, TokenType.NEWLINE))
                            result.append(Token(Lexemes.NEWLINE, TokenType.NEWLINE))
                    result.append(token)
                    first_table_after_from = False
                    i += 1
                    continue
                if first_table_after_from and token.type not in (
                    TokenType.WHITESPACE,
                    TokenType.NEWLINE,
                    TokenType.KEYWORD,
                ):
                    first_table_after_from = False
                result.append(token)
                i += 1
                continue
            result.append(token)
            i += 1
        return result


class OnNewlinesRule(BaseRule):
    """Place ON keyword on a new line after JOIN clauses."""

    rule_type = "tidy"
    order = 26
    supports_token_objects = True

    config_fields = {
        "on_newlines": ConfigField(
            name="on_newlines",
            default=True,
            description="Place ON keyword on new line after JOIN clauses?",
            field_type=bool,
        )
    }

    JOIN_KEYWORDS = {
        "INNER",
        "LEFT",
        "RIGHT",
        "FULL",
        "CROSS",
        "OUTER",
        "JOIN",
        "APPLY",
    }

    def apply(
        self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext
    ) -> List[Union[Token, TokenGroup]]:
        if not getattr(
            ctx.config, "on_newlines", self.config_fields["on_newlines"].default
        ):
            return tokens
        return self._process_tokens(tokens, in_join=False)

    def _process_tokens(
        self, tokens: List[Union[Token, TokenGroup]], in_join: bool = False
    ) -> List[Union[Token, TokenGroup]]:
        result: List[Union[Token, TokenGroup]] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if isinstance(token, TokenGroup):
                if token.group_type == GroupType.ON_CONDITION:
                    while (
                        result
                        and isinstance(result[-1], Token)
                        and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE)
                    ):
                        result.pop()
                    result.append(Token(Lexemes.NEWLINE, TokenType.NEWLINE))
                    processed = self._process_tokens(token.tokens, in_join)
                    result.append(
                        TokenGroup(
                            token.group_type, processed, token.name, token.metadata
                        )
                    )
                    i += 1
                    continue
                processed = self._process_tokens(token.tokens, in_join)
                result.append(
                    TokenGroup(token.group_type, processed, token.name, token.metadata)
                )
                i += 1
                continue
            if isinstance(token, Token):
                if (
                    token.type == TokenType.KEYWORD
                    and token.value.upper() in self.JOIN_KEYWORDS
                ):
                    in_join = True
                    result.append(token)
                    i += 1
                    continue
                if (
                    in_join
                    and token.type == TokenType.KEYWORD
                    and token.value.upper() == "ON"
                ):
                    while (
                        result
                        and isinstance(result[-1], Token)
                        and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE)
                    ):
                        result.pop()
                    result.append(Token(Lexemes.NEWLINE, TokenType.NEWLINE))
                    result.append(token)
                    in_join = False
                    i += 1
                    while (
                        i < len(tokens)
                        and isinstance(tokens[i], Token)
                        and tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE)
                    ):
                        i += 1
                    if i < len(tokens):
                        result.append(Token(Lexemes.SPACE, TokenType.WHITESPACE))
                    continue
                if in_join and token.type == TokenType.KEYWORD:
                    keyword = token.value.upper()
                    if keyword in (
                        "WHERE",
                        "GROUP",
                        "HAVING",
                        "ORDER",
                        "UNION",
                        "EXCEPT",
                        "INTERSECT",
                        "SELECT",
                        "FROM",
                    ):
                        in_join = False
                result.append(token)
                i += 1
                continue
            result.append(token)
            i += 1
        return result


class QuoteIdentifiersRule(BaseRule):
    """Add or normalize quotes around identifiers based on dialect."""

    rule_type = "tidy"
    order = 11
    supports_token_objects = True

    config_fields = {
        "quote_identifiers": ConfigField(
            name="quote_identifiers",
            default=False,
            description="Add quotes around identifiers (table/column names)?",
            field_type=bool,
        )
    }

    QUOTE_CHARS = {
        "sqlserver": ("[", "]"),
        "oracle": ('"', '"'),
        "postgresql": ('"', '"'),
        "mysql": ("`", "`"),
        "sqlite": ('"', '"'),
    }

    def _get_quote_chars(self, dialect: str):
        return self.QUOTE_CHARS.get(dialect, ('"', '"'))

    def _is_already_quoted(self, value: str) -> bool:
        return bool(
            value
            and len(value) >= 2
            and value[0] in ('"', "'", "[", "`")
            and value[-1] in ('"', "'", "]", "`")
        )

    def _quote_identifier(self, value: str, open_quote: str, close_quote: str) -> str:
        if "." in value:
            parts = value.split(".")
            quoted_parts = [f"{open_quote}{part}{close_quote}" for part in parts]
            return ".".join(quoted_parts)
        return f"{open_quote}{value}{close_quote}"

    def apply(
        self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext
    ) -> List[Union[Token, TokenGroup]]:
        if not getattr(ctx.config, "quote_identifiers", False):
            return tokens
        dialect = ctx.config.dialect
        open_quote, close_quote = self._get_quote_chars(dialect)
        return self._process_tokens(tokens, open_quote, close_quote)

    def _process_tokens(
        self, tokens: List[Union[Token, TokenGroup]], open_quote: str, close_quote: str
    ) -> List[Union[Token, TokenGroup]]:
        result: List[Union[Token, TokenGroup]] = []
        for token in tokens:
            if isinstance(token, Token):
                if token.type == TokenType.IDENTIFIER and not self._is_already_quoted(
                    token.value
                ):
                    quoted_value = self._quote_identifier(
                        token.value, open_quote, close_quote
                    )
                    result.append(Token(quoted_value, token.type))
                else:
                    result.append(token)
            elif isinstance(token, TokenGroup):
                processed = self._process_tokens(token.tokens, open_quote, close_quote)
                result.append(
                    TokenGroup(token.group_type, processed, token.name, token.metadata)
                )
            else:
                result.append(token)
        return result


class SelectNewlineRule(BaseRule):
    """Ensure SELECT keywords appear on their own line."""

    rule_type = "tidy"
    order = 35
    supports_token_objects = True

    config_fields = {
        "select_newline": ConfigField(
            name="select_newline",
            default=True,
            description="Add blank line before SELECT keywords?",
            field_type=bool,
        )
    }

    def apply(
        self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext
    ) -> List[Union[Token, TokenGroup]]:
        if not getattr(
            ctx.config, "select_newline", self.config_fields["select_newline"].default
        ):
            return tokens
        return self._process_tokens(tokens)

    def _process_tokens(
        self, tokens: List[Union[Token, TokenGroup]]
    ) -> List[Union[Token, TokenGroup]]:
        result: List[Union[Token, TokenGroup]] = []

        def first_token(group: TokenGroup):
            for it in group.tokens:
                if isinstance(it, Token):
                    return it
                if isinstance(it, TokenGroup):
                    ft = first_token(it)
                    if ft:
                        return ft
            return None

        i = 0
        while i < len(tokens):
            token = tokens[i]
            if isinstance(token, TokenGroup):
                processed_tokens = self._process_tokens(token.tokens)
                next_token = tokens[i + 1] if i + 1 < len(tokens) else None
                next_is_select = False
                if next_token:
                    if (
                        isinstance(next_token, Token)
                        and next_token.type == TokenType.KEYWORD
                        and next_token.value.upper() == "SELECT"
                    ):
                        next_is_select = True
                    elif isinstance(next_token, TokenGroup):
                        ft = first_token(next_token)
                        if (
                            ft
                            and ft.type == TokenType.KEYWORD
                            and ft.value.upper() == "SELECT"
                        ):
                            next_is_select = True
                if next_is_select and processed_tokens:
                    while (
                        processed_tokens
                        and isinstance(processed_tokens[-1], Token)
                        and processed_tokens[-1].type
                        in (TokenType.WHITESPACE, TokenType.NEWLINE)
                    ):
                        processed_tokens.pop()
                    processed_tokens.append(Token("\n", TokenType.NEWLINE))
                    processed_tokens.append(Token("\n", TokenType.NEWLINE))
                group_out = TokenGroup(
                    token.group_type, processed_tokens, token.name, token.metadata
                )
                result.append(group_out)
                i += 1
                continue
            result.append(token)
            i += 1
        return result


class ColumnsNewlineRule(BaseRule):
    """Format SELECT columns with each column on its own line."""

    rule_type = "tidy"
    order = 36
    supports_token_objects = True

    config_fields = {
        "columns_newline": ConfigField(
            name="columns_newline",
            default=True,
            description="Place each SELECT column on its own line?",
            field_type=bool,
        )
    }

    def apply(
        self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext
    ) -> List[Union[Token, TokenGroup]]:
        enabled = getattr(
            ctx.config, "columns_newline", self.config_fields["columns_newline"].default
        )
        if not enabled:
            return tokens
        return self._process_tokens(
            tokens, in_select=False, in_group=False, first_column_seen=False
        )

    def _process_tokens(
        self,
        tokens: List[Union[Token, TokenGroup]],
        in_select: bool = False,
        in_group: bool = False,
        first_column_seen: bool = False,
    ) -> List[Union[Token, TokenGroup]]:
        result: List[Union[Token, TokenGroup]] = []
        i = 0
        just_finished_select_clause = False
        while i < len(tokens):
            token = tokens[i]
            if isinstance(token, TokenGroup):
                # Check if this is a SELECT clause (generic CLAUSE that starts with SELECT)
                is_select_clause = False
                if token.group_type in (GroupType.SELECT_CLAUSE, GroupType.CLAUSE):
                    if token.tokens:
                        first_token = token.tokens[0]
                        if (
                            isinstance(first_token, Token)
                            and first_token.type == TokenType.KEYWORD
                            and first_token.value.upper() == "SELECT"
                        ):
                            is_select_clause = True

                # Check if this is a FROM clause (generic CLAUSE that starts with FROM)
                is_from_clause = False
                if token.group_type in (GroupType.FROM_CLAUSE, GroupType.CLAUSE):
                    if token.tokens:
                        first_token = token.tokens[0]
                        if (
                            isinstance(first_token, Token)
                            and first_token.type == TokenType.KEYWORD
                            and first_token.value.upper() in ("FROM", "INTO")
                        ):
                            is_from_clause = True

                if is_select_clause:
                    processed_tokens = self._process_tokens(
                        token.tokens,
                        in_select=True,
                        in_group=in_group,
                        first_column_seen=False,
                    )
                    if (
                        processed_tokens
                        and isinstance(processed_tokens[-1], Token)
                        and processed_tokens[-1].type != TokenType.NEWLINE
                    ):
                        processed_tokens = processed_tokens + [
                            Token("\n", TokenType.NEWLINE)
                        ]
                    result.append(
                        TokenGroup(
                            token.group_type,
                            processed_tokens,
                            token.name,
                            token.metadata,
                        )
                    )
                    just_finished_select_clause = True
                elif is_from_clause and just_finished_select_clause:
                    # Add blank line before FROM clause
                    while (
                        result
                        and isinstance(result[-1], Token)
                        and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE)
                    ):
                        result.pop()
                    result.append(Token("\n", TokenType.NEWLINE))
                    processed_tokens = self._process_tokens(
                        token.tokens,
                        in_select=in_select,
                        in_group=in_group,
                        first_column_seen=first_column_seen,
                    )
                    result.append(
                        TokenGroup(
                            token.group_type,
                            processed_tokens,
                            token.name,
                            token.metadata,
                        )
                    )
                    just_finished_select_clause = False
                elif token.group_type in (
                    GroupType.PARENTHESIS,
                    GroupType.SUBQUERY,
                    GroupType.FUNCTION,
                ):
                    processed_tokens = self._process_tokens(
                        token.tokens,
                        in_select=in_select,
                        in_group=True,
                        first_column_seen=first_column_seen,
                    )
                    result.append(
                        TokenGroup(
                            token.group_type,
                            processed_tokens,
                            token.name,
                            token.metadata,
                        )
                    )
                    just_finished_select_clause = False
                else:
                    processed_tokens = self._process_tokens(
                        token.tokens,
                        in_select=in_select,
                        in_group=in_group,
                        first_column_seen=first_column_seen,
                    )
                    result.append(
                        TokenGroup(
                            token.group_type,
                            processed_tokens,
                            token.name,
                            token.metadata,
                        )
                    )
                    just_finished_select_clause = False
                i += 1
                continue
            if isinstance(token, Token):
                if token.type == TokenType.KEYWORD and token.value.upper() == "SELECT":
                    in_select = True
                    first_column_seen = False
                    result.append(token)
                    i += 1
                    while (
                        i < len(tokens)
                        and isinstance(tokens[i], Token)
                        and tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE)
                    ):
                        i += 1
                    result.append(Token("\n", TokenType.NEWLINE))
                    just_finished_select_clause = False
                    continue
                # Handle FROM that comes after SELECT_CLAUSE group
                if (
                    just_finished_select_clause
                    and token.type == TokenType.KEYWORD
                    and token.value.upper() in ("FROM", "INTO")
                ):
                    while (
                        result
                        and isinstance(result[-1], Token)
                        and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE)
                    ):
                        result.pop()
                    result.append(Token("\n", TokenType.NEWLINE))
                    result.append(token)
                    i += 1
                    just_finished_select_clause = False
                    continue
                if in_select and not in_group and token.type == TokenType.KEYWORD:
                    keyword = token.value.upper()
                    if keyword in (
                        "FROM",
                        "INTO",
                        "WHERE",
                        "GROUP",
                        "ORDER",
                        "HAVING",
                        "UNION",
                        "EXCEPT",
                        "INTERSECT",
                    ):
                        in_select = False
                        first_column_seen = False
                        while (
                            result
                            and isinstance(result[-1], Token)
                            and result[-1].type
                            in (TokenType.WHITESPACE, TokenType.NEWLINE)
                        ):
                            result.pop()
                        result.append(Token("\n", TokenType.NEWLINE))
                        result.append(Token("\n", TokenType.NEWLINE))
                        result.append(token)
                        i += 1
                        just_finished_select_clause = False
                        continue
                # Also handle FROM inside parentheses/subqueries (CTEs, inline subqueries)
                if in_select and in_group and token.type == TokenType.KEYWORD:
                    keyword = token.value.upper()
                    if keyword in ("FROM", "INTO"):
                        while (
                            result
                            and isinstance(result[-1], Token)
                            and result[-1].type
                            in (TokenType.WHITESPACE, TokenType.NEWLINE)
                        ):
                            result.pop()
                        result.append(Token("\n", TokenType.NEWLINE))
                        result.append(Token("\n", TokenType.NEWLINE))
                        result.append(token)
                        i += 1
                        continue
                if (
                    in_select
                    and not in_group
                    and token.type == TokenType.PUNCTUATION
                    and token.value == ","
                ):
                    result.append(token)
                    i += 1
                    while (
                        i < len(tokens)
                        and isinstance(tokens[i], Token)
                        and tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE)
                    ):
                        i += 1
                    result.append(Token("\n", TokenType.NEWLINE))
                    first_column_seen = True
                    continue
                if (
                    in_select
                    and not first_column_seen
                    and not in_group
                    and token.type
                    not in (TokenType.WHITESPACE, TokenType.NEWLINE, TokenType.COMMENT)
                ):
                    first_column_seen = True
                    result.append(token)
                    i += 1
                    continue
                # Don't reset just_finished_select_clause for whitespace
                if token.type not in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    just_finished_select_clause = False
                result.append(token)
                i += 1
                continue
            result.append(token)
            i += 1
        return result


class WhereNewlinesRule(BaseRule):
    """Format WHERE clauses with newlines before AND/OR operators."""

    rule_type = "tidy"
    order = 30
    supports_token_objects = True

    config_fields = {
        "where_newlines": ConfigField(
            name="where_newlines",
            default=True,
            description="Add newlines before AND/OR operators in WHERE clauses?",
            field_type=bool,
        )
    }

    LOGICAL_OPERATORS = {"AND", "OR"}
    CLAUSE_TERMINATORS = {
        "GROUP",
        "HAVING",
        "ORDER",
        "UNION",
        "EXCEPT",
        "INTERSECT",
        "LIMIT",
        "OFFSET",
        "FETCH",
        "FOR",
        "OPTION",
    }

    def apply(
        self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext
    ) -> List[Union[Token, TokenGroup]]:
        if not getattr(
            ctx.config, "where_newlines", self.config_fields["where_newlines"].default
        ):
            return tokens
        return self._process_tokens(tokens, in_where=False, in_group=False)

    def _process_tokens(
        self,
        tokens: List[Union[Token, TokenGroup]],
        in_where: bool = False,
        in_group: bool = False,
    ) -> List[Union[Token, TokenGroup]]:
        result: List[Union[Token, TokenGroup]] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if isinstance(token, TokenGroup):
                # Check if this group starts with WHERE keyword
                starts_with_where = False
                if token.tokens:
                    first_token = token.tokens[0]
                    if (
                        isinstance(first_token, Token)
                        and first_token.type == TokenType.KEYWORD
                        and first_token.value.upper() == "WHERE"
                    ):
                        starts_with_where = True

                # Add blank line before WHERE clause
                if starts_with_where:
                    if result:
                        last_is_newline = (
                            isinstance(result[-1], Token)
                            and result[-1].type == TokenType.NEWLINE
                        )
                        if not last_is_newline:
                            while (
                                result
                                and isinstance(result[-1], Token)
                                and result[-1].type == TokenType.WHITESPACE
                            ):
                                result.pop()
                            result.append(Token("\n", TokenType.NEWLINE))
                            result.append(Token("\n", TokenType.NEWLINE))

                if token.group_type == GroupType.WHERE_CLAUSE:
                    processed = self._process_tokens(
                        token.tokens, in_where=True, in_group=in_group
                    )
                    result.append(
                        TokenGroup(
                            token.group_type, processed, token.name, token.metadata
                        )
                    )
                elif token.group_type in (
                    GroupType.PARENTHESIS,
                    GroupType.SUBQUERY,
                    GroupType.FUNCTION,
                ):
                    processed = self._process_tokens(
                        token.tokens, in_where=in_where, in_group=True
                    )
                    result.append(
                        TokenGroup(
                            token.group_type, processed, token.name, token.metadata
                        )
                    )
                else:
                    processed = self._process_tokens(
                        token.tokens, in_where=in_where, in_group=in_group
                    )
                    result.append(
                        TokenGroup(
                            token.group_type, processed, token.name, token.metadata
                        )
                    )
                i += 1
                continue
            if isinstance(token, Token):
                if token.type == TokenType.KEYWORD and token.value.upper() == "WHERE":
                    if result:
                        last_is_newline = (
                            isinstance(result[-1], Token)
                            and result[-1].type == TokenType.NEWLINE
                        )
                        if not last_is_newline:
                            while (
                                result
                                and isinstance(result[-1], Token)
                                and result[-1].type == TokenType.WHITESPACE
                            ):
                                result.pop()
                            result.append(Token("\n", TokenType.NEWLINE))
                            result.append(Token("\n", TokenType.NEWLINE))
                    in_where = True
                    result.append(token)
                    i += 1
                    continue
                if in_where and not in_group and token.type == TokenType.KEYWORD:
                    keyword = token.value.upper()
                    if keyword in self.CLAUSE_TERMINATORS:
                        in_where = False
                if in_where and not in_group and token.type == TokenType.KEYWORD:
                    keyword = token.value.upper()
                    if keyword in self.LOGICAL_OPERATORS:
                        while (
                            result
                            and isinstance(result[-1], Token)
                            and result[-1].type
                            in (TokenType.WHITESPACE, TokenType.NEWLINE)
                        ):
                            result.pop()
                        result.append(Token("\n", TokenType.NEWLINE))
                        result.append(token)
                        i += 1
                        while (
                            i < len(tokens)
                            and isinstance(tokens[i], Token)
                            and tokens[i].type
                            in (TokenType.WHITESPACE, TokenType.NEWLINE)
                        ):
                            i += 1
                        if i < len(tokens):
                            result.append(Token(" ", TokenType.WHITESPACE))
                        continue
                result.append(token)
                i += 1
                continue
            result.append(token)
            i += 1
        return result


class IndentSelectColumnsRule(BaseRule):
    """Add indentation to each selected column."""

    rule_type = "tidy"
    order = 50
    supports_token_objects = True

    config_fields = {
        "indent_select_columns": ConfigField(
            name="indent_select_columns",
            default=True,
            description="Add indentation to SELECT column lists?",
            field_type=bool,
        )
    }

    def apply(self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext):
        if not getattr(
            ctx.config,
            "indent_select_columns",
            self.config_fields["indent_select_columns"].default,
        ):
            return tokens
        return self._process_tokens(
            tokens, in_select=False, indent_str=ctx.get_indent_string()
        )

    def _process_tokens(
        self,
        tokens: List[Union[Token, TokenGroup]],
        in_select: bool = False,
        indent_str: str = "    ",
    ) -> List[Union[Token, TokenGroup]]:
        result: List[Union[Token, TokenGroup]] = []
        i = 0
        while i < len(tokens):
            token = tokens[i]
            if isinstance(token, TokenGroup):
                if token.group_type == GroupType.SELECT_CLAUSE:
                    processed_tokens = self._process_tokens(
                        token.tokens, in_select=True
                    )
                    result.append(
                        TokenGroup(
                            token.group_type,
                            processed_tokens,
                            token.name,
                            token.metadata,
                        )
                    )
                else:
                    processed_tokens = self._process_tokens(
                        token.tokens, in_select=in_select
                    )
                    result.append(
                        TokenGroup(
                            token.group_type,
                            processed_tokens,
                            token.name,
                            token.metadata,
                        )
                    )
                i += 1
                continue
            if isinstance(token, Token):
                if token.type == TokenType.KEYWORD and token.value.upper() == "SELECT":
                    in_select = True
                    result.append(token)
                    i += 1
                    continue
                if (
                    token.type == TokenType.KEYWORD
                    and token.value.upper() == "FROM"
                    and in_select
                ):
                    in_select = False
                    while (
                        result
                        and isinstance(result[-1], Token)
                        and result[-1].type == TokenType.WHITESPACE
                        and result[-1].value == "    "
                    ):
                        result.pop()
                    result.append(token)
                    i += 1
                    continue
                if in_select and token.type == TokenType.NEWLINE:
                    result.append(token)
                    # Skip any existing whitespace after the newline
                    next_idx = i + 1
                    while (
                        next_idx < len(tokens)
                        and isinstance(tokens[next_idx], Token)
                        and tokens[next_idx].type
                        in (TokenType.WHITESPACE, TokenType.NEWLINE)
                    ):
                        next_idx += 1
                    add_indent = True
                    if next_idx < len(tokens):
                        next_token = tokens[next_idx]
                        if (
                            isinstance(next_token, Token)
                            and next_token.type == TokenType.KEYWORD
                        ):
                            if next_token.value.upper() in (
                                "FROM",
                                "WHERE",
                                "GROUP",
                                "ORDER",
                                "HAVING",
                                "UNION",
                                "INTO",
                            ):
                                add_indent = False
                    if add_indent:
                        result.append(Token(indent_str, TokenType.WHITESPACE))
                    # Move past the whitespace we skipped
                    i = next_idx
                    continue
                result.append(token)
                i += 1
                continue
            result.append(token)
            i += 1
        return result


class CaseWhenNewlineIndentRule(BaseRule):
    """Format CASE expressions with newlines and indentation using construct matching."""

    rule_type = "tidy"
    order = 51  # Run after IndentSelectColumnsRule (50) to preserve CASE indentation
    supports_token_objects = True

    config_fields = {
        "case_when_newline_indent": ConfigField(
            name="case_when_newline_indent",
            default=True,
            description="Format CASE expressions with newlines and indentation?",
            field_type=bool,
        )
    }

    def apply(
        self, tokens: List[Union[Token, TokenGroup]], ctx: FormatterContext
    ) -> List[Union[Token, TokenGroup]]:
        if not getattr(
            ctx.config,
            "case_when_newline_indent",
            self.config_fields["case_when_newline_indent"].default,
        ):
            return tokens

        # Check if we have CASE_EXPRESSION constructs available
        case_constructs = self.get_constructs(ctx, "CASE_EXPRESSION")

        # Get indent string from context
        indent_str = ctx.get_indent_string()

        if case_constructs:
            # Use construct-aware processing for better accuracy
            return self._process_tokens_with_constructs(
                tokens, case_constructs, indent_str
            )
        else:
            # Fallback to token-based processing
            return self._process_tokens(tokens, indent_str)

    def _process_tokens_with_constructs(
        self,
        tokens: List[Union[Token, TokenGroup]],
        case_constructs: List[Dict],
        indent_str: str = "    ",
    ) -> List[Union[Token, TokenGroup]]:
        """Process tokens using construct information for more accurate formatting."""
        # Build set of positions where CASE expressions occur
        case_positions = set()
        for construct in case_constructs:
            case_positions.add(construct["start"])

        # Use the regular token-based processing but with construct awareness
        # This helps handle nested CASE expressions correctly
        return self._process_tokens(tokens, indent_str, case_positions)

    def _process_tokens(
        self,
        tokens: List[Union[Token, TokenGroup]],
        indent_str: str = "    ",
        case_positions: Optional[set] = None,
    ) -> List[Union[Token, TokenGroup]]:
        """Process tokens to format CASE expressions."""
        result: List[Union[Token, TokenGroup]] = []
        i = 0
        in_case = False
        case_depth = 0

        while i < len(tokens):
            token = tokens[i]

            if isinstance(token, TokenGroup):
                processed_group = TokenGroup(
                    token.group_type,
                    self._process_tokens(token.tokens, indent_str, case_positions),
                    token.name,
                    token.metadata,
                )
                result.append(processed_group)
                i += 1
                continue

            if (
                isinstance(token, Token)
                and token.type == TokenType.KEYWORD
                and token.value.upper() == "CASE"
            ):
                case_depth += 1
                in_case = True
                result.append(token)
                i += 1
                result.append(Token("\n", TokenType.NEWLINE))
                while (
                    i < len(tokens)
                    and isinstance(tokens[i], Token)
                    and tokens[i].type in (TokenType.WHITESPACE, TokenType.NEWLINE)
                ):
                    i += 1
                continue

            if (
                in_case
                and isinstance(token, Token)
                and token.type == TokenType.KEYWORD
                and token.value.upper() == "WHEN"
            ):
                while (
                    result
                    and isinstance(result[-1], Token)
                    and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE)
                ):
                    result.pop()
                result.append(Token("\n", TokenType.NEWLINE))
                # Double indent for WHEN clauses
                result.append(Token(indent_str + indent_str, TokenType.WHITESPACE))
                result.append(token)
                i += 1
                continue

            if (
                in_case
                and isinstance(token, Token)
                and token.type == TokenType.KEYWORD
                and token.value.upper() == "ELSE"
            ):
                while (
                    result
                    and isinstance(result[-1], Token)
                    and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE)
                ):
                    result.pop()
                result.append(Token("\n", TokenType.NEWLINE))
                # Double indent for ELSE clause
                result.append(Token(indent_str + indent_str, TokenType.WHITESPACE))
                result.append(token)
                i += 1
                continue

            if (
                isinstance(token, Token)
                and token.type == TokenType.KEYWORD
                and token.value.upper() == "END"
            ):
                if case_depth > 0:
                    case_depth -= 1
                    if case_depth == 0:
                        in_case = False
                    while (
                        result
                        and isinstance(result[-1], Token)
                        and result[-1].type in (TokenType.WHITESPACE, TokenType.NEWLINE)
                    ):
                        result.pop()
                    result.append(Token(" ", TokenType.WHITESPACE))
                    result.append(token)
                    i += 1
                    continue

            result.append(token)
            i += 1
        return result


class LeadingCommasRule(BaseRule):
    """Move commas to leading position in column lists when configured."""

    rule_type = "tidy"
    order = 45
    supports_token_objects = True

    config_fields = {
        "leading_commas": ConfigField(
            name="leading_commas",
            default=True,
            description="Use leading commas in column lists (e.g., col1\n  , col2\n  , col3)?",
            field_type=bool,
        )
    }

    def apply(
        self,
        tokens: Union[List[str], List[Union[Token, TokenGroup]]],
        ctx: FormatterContext,
    ) -> Union[List[str], List[Union[Token, TokenGroup]]]:
        leading = getattr(
            ctx.config, "leading_commas", self.config_fields["leading_commas"].default
        )
        if not leading:
            return tokens
        if not tokens or isinstance(tokens[0], str):
            sql = "".join(tokens)
            typed_tokens = tokenize_with_types(
                sql, ctx.config.dialect, SemanticLevel.BASIC
            )
            flat_tokens = self._flatten_tokens(typed_tokens)
        else:
            flat_tokens = self._flatten_tokens(tokens)
        result: List[Token] = []
        i = 0
        while i < len(flat_tokens):
            token = flat_tokens[i]
            if token.type == TokenType.PUNCTUATION and token.value == ",":
                j = i + 1
                has_newline = False
                whitespace_tokens: List[Token] = []
                newline_count = 0
                while j < len(flat_tokens) and flat_tokens[j].type in (
                    TokenType.WHITESPACE,
                    TokenType.NEWLINE,
                ):
                    if flat_tokens[j].type == TokenType.NEWLINE:
                        has_newline = True
                        newline_count += 1
                        if newline_count == 1:
                            whitespace_tokens.append(flat_tokens[j])
                    else:
                        whitespace_tokens.append(flat_tokens[j])
                    j += 1
                if has_newline and whitespace_tokens:
                    while result and result[-1].type in (
                        TokenType.WHITESPACE,
                        TokenType.NEWLINE,
                    ):
                        result.pop()
                    result.extend(whitespace_tokens)
                    result.append(token)
                    i = j
                    continue
            result.append(token)
            i += 1
        return result

    def _flatten_tokens(self, tokens: List[Union[Token, TokenGroup]]) -> List[Token]:
        from sqltidy.tokenizer import GroupType as LocalGroupType

        result: List[Token] = []
        for item in tokens:
            if isinstance(item, Token):
                result.append(item)
            elif isinstance(item, TokenGroup):
                if item.group_type in (
                    LocalGroupType.PARENTHESIS,
                    LocalGroupType.SUBQUERY,
                ):
                    result.append(Token("(", TokenType.PUNCTUATION))
                    result.extend(self._flatten_tokens(item.tokens))
                    result.append(Token(")", TokenType.PUNCTUATION))
                elif item.group_type == LocalGroupType.FUNCTION:
                    if item.tokens:
                        result.append(item.tokens[0])
                        result.append(Token("(", TokenType.PUNCTUATION))
                        result.extend(self._flatten_tokens(item.tokens[1:]))
                        result.append(Token(")", TokenType.PUNCTUATION))
                else:
                    result.extend(self._flatten_tokens(item.tokens))
        return result


class AliasStyleABCRule(BaseRule):
    """Convert table aliases to alphabetic style (A, B, C...)."""

    rule_type = "rewrite"
    order = 8

    config_fields = {
        "enable_alias_style_abc": ConfigField(
            name="enable_alias_style_abc",
            default=False,
            description="Convert table aliases to alphabetic style (A, B, C, ...)?",
            field_type=bool,
        )
    }

    def _extract_cte_scopes(self, sql: str):
        scopes = []
        with_match = re.search(r"\bWITH\s+", sql, re.IGNORECASE)
        if not with_match:
            return [(sql, 0, len(sql))]
        pos = with_match.end()
        cte_pattern = re.compile(r"(\w+)\s+AS\s*\(", re.IGNORECASE)
        while pos < len(sql):
            cte_match = cte_pattern.search(sql, pos)
            if not cte_match:
                if pos < len(sql):
                    scopes.append((sql[pos:], pos, len(sql)))
                break
            paren_start = cte_match.end() - 1
            paren_count = 1
            i = paren_start + 1
            while i < len(sql) and paren_count > 0:
                if sql[i] == "(":
                    paren_count += 1
                elif sql[i] == ")":
                    paren_count -= 1
                i += 1
            cte_start_pos = cte_match.end()
            cte_end_pos = i - 1
            cte_content = sql[cte_start_pos:cte_end_pos]
            scopes.append((cte_content, cte_start_pos, cte_end_pos))
            pos = i
            while pos < len(sql) and sql[pos].isspace():
                pos += 1
            if pos < len(sql) and sql[pos] == ",":
                pos += 1
            # Check if another CTE follows (with or without comma)
            next_cte_match = cte_pattern.search(sql, pos)
            if next_cte_match and next_cte_match.start() == pos:
                # Another CTE immediately follows, continue the loop
                continue
            # No more CTEs, append the rest as the main query scope
            if pos < len(sql):
                scopes.append((sql[pos:], pos, len(sql)))
            break
        return scopes

    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "enable_alias_style_abc", False):
            return tokens
        # Store dialect for use in _apply_to_scope_text
        self._dialect = ctx.config.dialect
        sql = "".join(tokens)
        scopes = self._extract_cte_scopes(sql)
        result_sql = sql
        offset = 0
        for scope_sql, start_pos, end_pos in scopes:
            new_scope_sql = self._apply_to_scope_text(scope_sql)
            actual_start = start_pos + offset
            actual_end = end_pos + offset
            result_sql = (
                result_sql[:actual_start] + new_scope_sql + result_sql[actual_end:]
            )
            offset += len(new_scope_sql) - len(scope_sql)

        return result_sql

    def _apply_to_scope_text(self, sql: str) -> str:
        def _num_to_letters(n: int) -> str:
            letters = []
            n += 1
            while n > 0:
                n, rem = divmod(n - 1, 26)
                letters.append(chr(ord("A") + rem))
            return "".join(reversed(letters))

        # Get SQL keywords from dialect to avoid treating them as aliases
        from ..dialects import get_dialect

        dialect = get_dialect(self._dialect)
        sql_keywords = {kw.upper() for kw in dialect.keywords}

        # Build keyword pattern for negative lookahead
        keyword_pattern = "|".join(
            sorted(sql_keywords, key=len, reverse=True)
        )  # Longest first to avoid partial matches

        # Pattern to match FROM/JOIN with table and optional alias
        # Use negative lookahead to prevent matching SQL keywords as aliases
        pattern = re.compile(
            rf"\b(FROM|JOIN)\s+([A-Za-z_][\w\.]*)(?:\s+AS\s+([A-Za-z_][\w]*)|\s+(?!(?:{keyword_pattern})\b)([A-Za-z_][\w]*))?",
            re.IGNORECASE,
        )
        mappings: Dict[str, str] = {}
        counter = 0

        def _replacer(match):
            nonlocal counter
            kw = match.group(1)
            table = match.group(2)
            # Alias can be in group 3 (after AS) or group 4 (without AS)
            alias = match.group(3) or match.group(4)

            # Always use the table name as the base, not the existing alias
            base = table.split(".")[-1]
            if base not in mappings:
                mappings[base] = _num_to_letters(counter)
                counter += 1
            new_alias = mappings[base]
            # Also map the old alias if it exists and is different from table name
            if alias and alias.upper() != base.upper():
                mappings[alias] = new_alias
            return f"{kw} {table} AS {new_alias}"

        new_sql = pattern.sub(_replacer, sql)
        if mappings:
            ref_pattern = re.compile(
                r"\b(" + "|".join(re.escape(k) for k in mappings.keys()) + r")\b(?=\.)"
            )
            new_sql = ref_pattern.sub(lambda m: mappings[m.group(1)], new_sql)
        return new_sql


class AliasStyleTNumericRule(BaseRule):
    """Convert table aliases to numeric style (T1, T2, T3...)."""

    rule_type = "rewrite"
    order = 9

    config_fields = {
        "enable_alias_style_t_numeric": ConfigField(
            name="enable_alias_style_t_numeric",
            default=False,
            description="Convert table aliases to numeric style (T1, T2, T3, ...)?",
            field_type=bool,
        )
    }

    def _extract_cte_scopes(self, sql: str):
        scopes = []
        with_match = re.search(r"\bWITH\s+", sql, re.IGNORECASE)
        if not with_match:
            return [(sql, 0, len(sql))]
        pos = with_match.end()
        cte_pattern = re.compile(r"(\w+)\s+AS\s*\(", re.IGNORECASE)
        while pos < len(sql):
            cte_match = cte_pattern.search(sql, pos)
            if not cte_match:
                if pos < len(sql):
                    scopes.append((sql[pos:], pos, len(sql)))
                break
            paren_start = cte_match.end() - 1
            paren_count = 1
            i = paren_start + 1
            while i < len(sql) and paren_count > 0:
                if sql[i] == "(":
                    paren_count += 1
                elif sql[i] == ")":
                    paren_count -= 1
                i += 1
            cte_start_pos = cte_match.end()
            cte_end_pos = i - 1
            cte_content = sql[cte_start_pos:cte_end_pos]
            scopes.append((cte_content, cte_start_pos, cte_end_pos))
            pos = i
            while pos < len(sql) and sql[pos].isspace():
                pos += 1
            if pos < len(sql) and sql[pos] == ",":
                pos += 1
            # Check if another CTE follows (with or without comma)
            next_cte_match = cte_pattern.search(sql, pos)
            if next_cte_match and next_cte_match.start() == pos:
                # Another CTE immediately follows, continue the loop
                continue
            # No more CTEs, append the rest as the main query scope
            if pos < len(sql):
                scopes.append((sql[pos:], pos, len(sql)))
            break
        return scopes

    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "enable_alias_style_t_numeric", False):
            return tokens
        # Store dialect for use in _apply_to_scope_text
        self._dialect = ctx.config.dialect
        sql = "".join(tokens)
        scopes = self._extract_cte_scopes(sql)
        result_sql = sql
        offset = 0
        for scope_sql, start_pos, end_pos in scopes:
            new_scope_sql = self._apply_to_scope_text(scope_sql)
            actual_start = start_pos + offset
            actual_end = end_pos + offset
            result_sql = (
                result_sql[:actual_start] + new_scope_sql + result_sql[actual_end:]
            )
            offset += len(new_scope_sql) - len(scope_sql)

        return result_sql

    def _apply_to_scope_text(self, sql: str) -> str:
        # Get SQL keywords from dialect to avoid treating them as aliases
        from ..dialects import get_dialect

        dialect = get_dialect(self._dialect)
        sql_keywords = {kw.upper() for kw in dialect.keywords}

        # Build keyword pattern for negative lookahead
        keyword_pattern = "|".join(
            sorted(sql_keywords, key=len, reverse=True)
        )  # Longest first to avoid partial matches

        # Pattern to match FROM/JOIN with table and optional alias
        # Use negative lookahead to prevent matching SQL keywords as aliases
        pattern = re.compile(
            rf"\b(FROM|JOIN)\s+([A-Za-z_][\w\.]*)(?:\s+AS\s+([A-Za-z_][\w]*)|\s+(?!(?:{keyword_pattern})\b)([A-Za-z_][\w]*))?",
            re.IGNORECASE,
        )
        mappings: Dict[str, str] = {}
        counter = 0

        def _replacer(match):
            nonlocal counter
            kw = match.group(1)
            table = match.group(2)
            # Alias can be in group 3 (after AS) or group 4 (without AS)
            alias = match.group(3) or match.group(4)

            # Always use the table name as the base, not the existing alias
            base = table.split(".")[-1]
            if base not in mappings:
                mappings[base] = f"T{counter + 1}"
                counter += 1
            new_alias = mappings[base]
            # Also map the old alias if it exists and is different from table name
            if alias and alias.upper() != base.upper():
                mappings[alias] = new_alias
            return f"{kw} {table} AS {new_alias}"

        new_sql = pattern.sub(_replacer, sql)
        if mappings:
            ref_pattern = re.compile(
                r"\b(" + "|".join(re.escape(k) for k in mappings.keys()) + r")\b(?=\.)"
            )
            new_sql = ref_pattern.sub(lambda m: mappings[m.group(1)], new_sql)
        return new_sql


class SubqueryToCTERule(BaseRule):
    """Convert subqueries to Common Table Expressions (CTEs) using construct matching."""

    rule_type = "rewrite"
    order = 5

    config_fields = {
        "enable_subquery_to_cte": ConfigField(
            name="enable_subquery_to_cte",
            default=False,
            description="Convert subqueries to Common Table Expressions (CTEs)?",
            field_type=bool,
        )
    }

    def _find_balanced_subquery(self, sql: str, start_pos: int) -> Optional[Dict]:
        """Find a balanced subquery starting at start_pos (which should be at '(')."""
        if start_pos >= len(sql) or sql[start_pos] != "(":
            return None

        # Check if SELECT follows the opening paren
        i = start_pos + 1
        while i < len(sql) and sql[i] in " \t\n\r":
            i += 1

        if i >= len(sql) - 6 or sql[i : i + 6].upper() != "SELECT":
            return None

        # Find matching closing paren
        paren_depth = 1
        pos = start_pos + 1
        while pos < len(sql) and paren_depth > 0:
            if sql[pos] == "(":
                paren_depth += 1
            elif sql[pos] == ")":
                paren_depth -= 1
            pos += 1

        if paren_depth != 0:
            return None

        # Extract content
        full_text = sql[start_pos:pos]
        content = sql[start_pos + 1 : pos - 1].strip()

        # Check for optional alias
        alias = None
        alias_end = pos
        j = pos
        while j < len(sql) and sql[j] in " \t\n\r":
            j += 1
        if j < len(sql) - 2 and sql[j : j + 2].upper() == "AS":
            j += 2
            while j < len(sql) and sql[j] in " \t\n\r":
                j += 1
            alias_start = j
            while j < len(sql) and (sql[j].isalnum() or sql[j] == "_"):
                j += 1
            if j > alias_start:
                alias = sql[alias_start:j]
                alias_end = j

        return {
            "start": start_pos,
            "end": alias_end,
            "full": sql[start_pos:alias_end],
            "content": content,
            "alias": alias,
        }

    def _process_subqueries_recursively(
        self, sql: str, cte_num: int
    ) -> tuple[str, list[str], int]:
        """
        Recursively find and extract subqueries, returning the modified SQL,
        list of CTE definitions, and updated CTE counter.
        """
        # Find all subqueries in this SQL fragment
        subqueries = []
        i = 0
        while i < len(sql):
            if sql[i] == "(":
                subquery = self._find_balanced_subquery(sql, i)
                if subquery:
                    subqueries.append(subquery)
                    i = subquery["end"]
                    continue
            i += 1

        if not subqueries:
            return sql, [], cte_num

        # Process each subquery
        all_ctes = []
        replacements = []

        for subquery in subqueries:
            # First, recursively process nested subqueries within this subquery
            nested_sql, nested_ctes, cte_num = self._process_subqueries_recursively(
                subquery["content"], cte_num
            )

            # Add nested CTEs to our list
            all_ctes.extend(nested_ctes)

            # Generate CTE name for this subquery
            cte_name = f"cte_{cte_num}"
            cte_num += 1

            # Create CTE definition with potentially modified content
            cte_def = f"{cte_name} AS (\n    {nested_sql}\n)"
            all_ctes.append(cte_def)

            # Create replacement (preserve alias if it exists)
            replacement = cte_name
            if subquery["alias"]:
                replacement += f" AS {subquery['alias']}"

            replacements.append((subquery["start"], subquery["end"], replacement))

        # Apply replacements from end to start to preserve positions
        modified_sql = sql
        for start, end, replacement in reversed(replacements):
            modified_sql = modified_sql[:start] + replacement + modified_sql[end:]

        return modified_sql, all_ctes, cte_num

    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "enable_subquery_to_cte", False):
            return tokens

        sql = "".join(tokens)

        # Use constructs from context (already parsed by SQLFormatter)
        constructs = ctx.constructs if hasattr(ctx, "constructs") else []

        # Filter for CTE constructs
        cte_constructs = [c for c in constructs if c["name"] == "CTE"]

        # Determine starting CTE number based on existing CTEs
        initial_cte_num = len(cte_constructs) + 1

        # Process existing CTE definitions to extract subqueries within them
        existing_cte_new_ctes = []
        if cte_constructs:
            for cte in cte_constructs:
                # Extract the CTE's subquery content (the part inside AS (...))
                cte_subquery = cte["groups"].get("subquery", "")
                if cte_subquery:
                    # Recursively process subqueries within this CTE's definition
                    _, nested_ctes, initial_cte_num = (
                        self._process_subqueries_recursively(
                            cte_subquery, initial_cte_num
                        )
                    )
                    existing_cte_new_ctes.extend(nested_ctes)

        # Process subqueries in the main query part
        if cte_constructs:
            # Find end of existing CTE block
            last_cte = cte_constructs[-1]
            cte_end = last_cte["end"]
            existing_cte_block = sql[:cte_end]
            main_query = sql[cte_end:]

            # Recursively process subqueries in main query
            modified_main_query, main_query_ctes, final_cte_num = (
                self._process_subqueries_recursively(main_query, initial_cte_num)
            )

            # Combine all new CTEs
            all_new_ctes = existing_cte_new_ctes + main_query_ctes

            # If no new CTEs were created, return original
            if not all_new_ctes:
                return tokens

            # Append new CTEs after existing ones
            cte_block = (
                existing_cte_block.rstrip() + ",\n" + ",\n".join(all_new_ctes) + "\n"
            )
            result_sql = cte_block + modified_main_query
        else:
            # Recursively process all subqueries in the entire SQL
            modified_sql, new_ctes, final_cte_num = (
                self._process_subqueries_recursively(sql, initial_cte_num)
            )

            # If no new CTEs were created, return original
            if not new_ctes:
                return tokens

            # Create new WITH clause
            cte_block = "WITH " + ",\n".join(new_ctes) + "\n"
            result_sql = cte_block + modified_sql

        return result_sql


__all__ = [
    "UppercaseKeywordsRule",
    "CompactWhitespaceRule",
    "NewlineJoinPatternRule",
    "OnNewlinesRule",
    "QuoteIdentifiersRule",
    "SelectNewlineRule",
    "ColumnsNewlineRule",
    "WhereNewlinesRule",
    "IndentSelectColumnsRule",
    "CaseWhenNewlineIndentRule",
    "LeadingCommasRule",
    "AliasStyleABCRule",
    "AliasStyleTNumericRule",
    "SubqueryToCTERule",
]
