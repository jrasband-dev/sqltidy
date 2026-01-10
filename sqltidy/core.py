# sqltidy/core.py
from typing import List, Any, Union
from .rulebook import SQLTidyConfig
from .tokenizer import tokenize_with_types, Token, TokenGroup, SemanticLevel


class SQLFormatter:
    """Main SQL formatting engine."""

    def __init__(self, config: SQLTidyConfig = None, rule_type: str = None):
        """Initialize formatter.

        Args:
            config: Configuration for formatting.
            rule_type: Filter rules by type ('tidy' or 'rewrite'). None loads all.
        """
        from .rules import load_rules
        from .rules.base import FormatterContext

        self.ctx = FormatterContext(config or SQLTidyConfig())
        self.rules = load_rules(rule_type=rule_type)
        self.applied_rules = []  # Track which rules were actually applied

    def flatten_tokens(self, tokens: List[Union[Token, TokenGroup]]) -> str:
        """Convert Token/TokenGroup objects back to SQL string.

        Args:
            tokens: List of Token and/or TokenGroup objects

        Returns:
            Formatted SQL string
        """
        result = []
        for item in tokens:
            if isinstance(item, Token):
                result.append(item.value)
            elif isinstance(item, TokenGroup):
                result.append(item.get_text())
            elif isinstance(item, str):
                # Legacy support for string tokens
                result.append(item)
        return "".join(result).strip()

    def format(self, sql: str, return_metadata: bool = False) -> Any:
        """Format SQL and optionally return metadata about applied rules.

        Args:
            sql: SQL string to format
            return_metadata: If True, return dict with 'sql' and 'applied_rules'

        Returns:
            Formatted SQL string, or dict with metadata if return_metadata=True
        """
        # Tokenize once using semantic tokenizer
        tokens = tokenize_with_types(
            sql, self.ctx.config.dialect, SemanticLevel.SEMANTIC
        )

        self.applied_rules = []  # Reset for each format call
        all_applicable_rules = []  # Track all rules that could have been applied

        # Apply rules that are applicable to the current dialect
        for rule in sorted(self.rules, key=lambda r: getattr(r, "order", 100)):
            if rule.is_applicable(self.ctx):
                all_applicable_rules.append(
                    {
                        "name": rule.__class__.__name__,
                        "type": getattr(rule, "rule_type", "unknown"),
                        "order": getattr(rule, "order", 100),
                    }
                )

                old_tokens = tokens

                # Check if rule supports Token objects or needs legacy string tokens
                if (
                    hasattr(rule, "supports_token_objects")
                    and rule.supports_token_objects
                ):
                    # New Token-based API
                    tokens = rule.apply(tokens, self.ctx)
                else:
                    # Legacy string-based API - convert to strings, apply rule, convert back
                    string_tokens = self._tokens_to_strings(tokens)
                    string_tokens = rule.apply(string_tokens, self.ctx)
                    # Re-tokenize to get Token objects back
                    tokens = tokenize_with_types(
                        "".join(string_tokens),
                        self.ctx.config.dialect,
                        SemanticLevel.SEMANTIC,
                    )

                # Track if rule actually changed anything
                if tokens != old_tokens:
                    self.applied_rules.append(
                        {
                            "name": rule.__class__.__name__,
                            "type": getattr(rule, "rule_type", "unknown"),
                            "order": getattr(rule, "order", 100),
                        }
                    )

        formatted_sql = self.flatten_tokens(tokens)

        if return_metadata:
            return {
                "sql": formatted_sql,
                "applied_rules": self.applied_rules,
                "all_applicable_rules": all_applicable_rules,
                "total_rules": len(self.rules),
                "applicable_rules": sum(
                    1 for r in self.rules if r.is_applicable(self.ctx)
                ),
            }

        return formatted_sql

    def _tokens_to_strings(self, tokens: List[Union[Token, TokenGroup]]) -> List[str]:
        """Convert Token/TokenGroup objects to simple string list for legacy rules.

        Args:
            tokens: List of Token and/or TokenGroup objects

        Returns:
            List of string tokens
        """

        def emit_from(items: List[Union[Token, TokenGroup]], out: List[str]):
            for it in items:
                if isinstance(it, Token):
                    out.append(it.value)
                elif isinstance(it, TokenGroup):
                    # Preserve structural markers for certain group types
                    if it.group_type in (getattr(self, "_GroupType", None) or []):
                        # Fallback if GroupType is not imported
                        pass
                    from sqltidy.tokenizer import GroupType

                    if it.group_type in (GroupType.PARENTHESIS, GroupType.SUBQUERY):
                        out.append("(")
                        emit_from(it.tokens, out)
                        out.append(")")
                    elif it.group_type == GroupType.FUNCTION:
                        # Expect first token is function name
                        func_name = ""
                        if it.tokens and isinstance(it.tokens[0], Token):
                            func_name = it.tokens[0].value
                        if func_name:
                            out.append(func_name)
                        out.append("(")
                        emit_from(it.tokens[1:] if it.tokens else [], out)
                        out.append(")")
                    else:
                        emit_from(it.tokens, out)

        result: List[str] = []
        emit_from(tokens, result)
        return result
