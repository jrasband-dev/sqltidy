# sqltidy/core.py
from typing import List, Any, Union
from .rulebook import SQLTidyConfig
from .tokenizer import tokenize_with_types, Token, TokenGroup, SemanticLevel, tokenize,TokenType
from .constructs.base import match_constructs


class SQLScript:
    """
    Represents a tokenized SQL script, including the original SQL,
    the list of tokens, and utility methods for further processing.
    """

    def __init__(self, sql: str, tokens: list, dialect: str = "sqlserver", constructs: list = None):
        self.sql = sql
        self._tokens = tokens  # List[Token] or List[str]
        self.dialect = dialect
        self._constructs = constructs if constructs is not None else [t.type if hasattr(t, 'type') else None for t in tokens]

    @classmethod
    def parse(cls, sql: str, dialect: str = "sqlserver") -> SQLScript:
        tokens = tokenize(sql, dialect)
        constructs = match_constructs(sql, dialect)


        return cls(sql, tokens, dialect, constructs)

    def __repr__(self):
        return self.sql
    
    def flatten(self) -> SQLScript:
        """Flatten multiple SQLScript instances into one."""
        # Assume self is a sequence of SQLScript objects
        if not hasattr(self, '__iter__') or isinstance(self, str):
            raise TypeError("flatten() should be called on a sequence of SQLScript objects")
        scripts = list(self)
        if not scripts:
            return SQLScript("", [], "sqlserver")
        combined_sql = "".join(ts.sql for ts in scripts)
        combined_tokens = []
        for ts in scripts:
            combined_tokens.extend(ts._tokens)
        dialect = scripts[0].dialect
        return SQLScript(combined_sql, combined_tokens, dialect)

    @property
    def tokens(self) -> List[dict]:
        """Return the list of tokens as dicts with value and type."""
        result = []
        for t in self._tokens:
            if hasattr(t, "value") and hasattr(t, "type"):
                result.append({"value": t.value, "type": t.type.name})

        return result
    
    @property
    def constructs(self) -> List[str]:
        """Return matched patterns and their Pattern names."""
        return self._constructs
        
        
    @property
    def token_list(self) -> List[Union[str, Token]]:
        """Return the list of tokens."""
        if self._tokens and hasattr(self._tokens[0], "value"):
            return [t.value for t in self._tokens]
        return list(self._tokens)
    
    @property
    def patterns(self) -> Optional[List[TokenType]]:
        """Return the list of token types (patterns) for the tokens."""
        return self._patterns







class SQLFormatter:
    """Main SQL formatting engine."""

    def __init__(self, config: SQLTidyConfig = None, rule_type: str = None):
        """Initialize formatter.

        Args:
            config: Configuration for formatting.
            rule_type: Filter rules by type ('tidy' or 'rewrite'). None loads all.
        """
        from .rules import load_rules
        from .rules.base import FormatterContext, BaseRule

        self.ctx = FormatterContext(config or SQLTidyConfig())
        loaded_rules = load_rules(rule_type=rule_type)
        
        # Filter to ensure only BaseRule instances (defensive programming)
        self.rules = [r for r in loaded_rules if isinstance(r, BaseRule)]
        
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
        # Parse SQL using SQLScript to get tokens and matched constructs
        script = SQLScript.parse(sql, self.ctx.config.dialect)
        
        # Set constructs in context so rules can access them
        self.ctx.constructs = script.constructs
        self.ctx.script = script
        
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
