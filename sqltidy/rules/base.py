from typing import List, Optional, Set, Dict, Any, Union
from dataclasses import dataclass
from ..rulebook import SQLTidyConfig
from ..tokenizer import Token, TokenGroup, TokenType, GroupType


@dataclass
class ConfigField:
    """
    Metadata for a configuration field used by a rule.

    Attributes:
        name: The config field name (e.g., 'uppercase_keywords')
        default: Default value for this field
        description: Human-readable description for interactive prompts
        field_type: Python type of the field (bool, str, int, etc.)
        dialect_defaults: Optional dict mapping dialect names to dialect-specific defaults
    """

    name: str
    default: Any
    description: str
    field_type: type = bool
    dialect_defaults: Optional[Dict[str, Any]] = None


class FormatterContext:
    """Holds configuration for the formatting run."""

    def __init__(self, config: SQLTidyConfig):
        self.config = config

    def get_indent_string(self) -> str:
        """
        Get the indentation string based on configuration.

        Returns:
            Tab character if use_tabs is True, otherwise the configured number of spaces.
            Defaults to 4 spaces if not configured.
        """
        use_tabs = getattr(self.config, "use_tabs", False)
        if use_tabs:
            return "\t"

        indent_size = getattr(self.config, "indent_size", 4)
        return " " * indent_size


class BaseRule:
    """
    Base class for all SQL formatting rules.

    Rules can be either 'tidy' (formatting without structural changes) or
    'rewrite' (transformations that change SQL structure).

    Token-based API:
        - New rules should set `supports_token_objects = True` and work with Token/TokenGroup objects
        - This allows rules to modify the token tree without re-tokenizing
        - Use helper methods like find_tokens(), replace_token(), insert_after(), etc.

    Legacy String API:
        - Rules without `supports_token_objects` continue to work with string tokens
        - The formatter will convert Token objects to strings before calling apply()
        - After apply(), strings are re-tokenized (slower, loses formatting from previous rules)

    Dialect Support:
        - Set `supported_dialects` to None (default) to support all dialects
        - Set to a set/list of dialect names to restrict rule to specific dialects
        - Override `is_applicable()` for complex dialect compatibility logic

    Configuration:
        - Set `config_fields` to declare configuration options this rule uses
        - This enables automatic config schema generation and validation

    Attributes:
        order (int): Execution order (lower numbers run first)
        rule_type (str): Either "tidy" or "rewrite"
        supports_token_objects (bool): If True, rule works with Token/TokenGroup objects
        supported_dialects (Optional[Set[str]]): Dialects this rule supports (None = all)
        config_fields (Optional[Dict[str, ConfigField]]): Configuration fields this rule uses
    """

    order: int = 100
    rule_type: Optional[str] = None  # "tidy" or "rewrite"
    supports_token_objects: bool = False  # Set to True for new Token-based rules
    supported_dialects: Optional[Set[str]] = None  # None = all dialects
    config_fields: Optional[Dict[str, ConfigField]] = None  # Configuration metadata

    def is_applicable(self, ctx: FormatterContext) -> bool:
        """
        Check if this rule applies to the current dialect.

        Override this method for complex dialect compatibility logic.
        The default implementation checks `supported_dialects`.

        Args:
            ctx: Formatter context containing configuration

        Returns:
            True if the rule should be applied, False otherwise
        """
        if self.supported_dialects is None:
            return True
        return ctx.config.dialect in self.supported_dialects

    def apply(
        self,
        tokens: Union[List[str], List[Union[Token, TokenGroup]]],
        ctx: FormatterContext,
    ) -> Union[List[str], List[Union[Token, TokenGroup]]]:
        """
        Apply the rule to the token list.

        This is the main entry point. Override this in subclasses.

        For Token-based rules (supports_token_objects=True):
            - tokens will be List[Union[Token, TokenGroup]]
            - Return List[Union[Token, TokenGroup]]

        For legacy string-based rules:
            - tokens will be List[str]
            - Return List[str]

        Args:
            tokens: List of SQL tokens (either strings or Token/TokenGroup objects)
            ctx: Formatter context containing configuration

        Returns:
            Modified list of tokens
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement apply() method"
        )

    # ==================== Helper methods for Token-based rules ====================

    def find_tokens(
        self,
        tokens: List[Union[Token, TokenGroup]],
        token_type: TokenType = None,
        value: str = None,
        group_type: GroupType = None,
    ) -> List[Union[Token, TokenGroup]]:
        """Find all tokens/groups matching criteria.

        Args:
            tokens: List to search
            token_type: Filter by token type (e.g., TokenType.KEYWORD)
            value: Filter by exact value (case-insensitive for keywords)
            group_type: Filter by group type (e.g., GroupType.SELECT_CLAUSE)

        Returns:
            List of matching tokens/groups
        """
        results = []
        for item in tokens:
            if isinstance(item, Token):
                if token_type and item.type != token_type:
                    continue
                if value:
                    if item.type == TokenType.KEYWORD:
                        if item.value.upper() != value.upper():
                            continue
                    elif item.value != value:
                        continue
                results.append(item)
            elif isinstance(item, TokenGroup):
                if group_type and item.group_type != group_type:
                    # Still search recursively
                    results.extend(
                        self.find_tokens(item.tokens, token_type, value, group_type)
                    )
                else:
                    if group_type:
                        results.append(item)
                    # Search within group
                    results.extend(
                        self.find_tokens(item.tokens, token_type, value, group_type)
                    )
        return results

    def flatten_tokens(self, tokens: List[Union[Token, TokenGroup]]) -> List[Token]:
        """Flatten token tree to simple list of Token objects.

        Args:
            tokens: List of Token and/or TokenGroup objects

        Returns:
            Flat list of Token objects
        """
        result = []
        for item in tokens:
            if isinstance(item, Token):
                result.append(item)
            elif isinstance(item, TokenGroup):
                result.extend(item.flatten())
        return result

    def get_text(self, tokens: List[Union[Token, TokenGroup]]) -> str:
        """Convert tokens to SQL text.

        Args:
            tokens: List of Token and/or TokenGroup objects

        Returns:
            SQL text
        """
        result = []
        for item in tokens:
            if isinstance(item, Token):
                result.append(item.value)
            elif isinstance(item, TokenGroup):
                result.append(item.get_text())
        return "".join(result)

    def insert_after(
        self,
        tokens: List[Union[Token, TokenGroup]],
        after: Union[Token, TokenGroup],
        new_tokens: List[Union[Token, TokenGroup]],
    ) -> List[Union[Token, TokenGroup]]:
        """Insert tokens after a specific token.

        Args:
            tokens: List to modify
            after: Token to insert after
            new_tokens: Tokens to insert

        Returns:
            Modified token list
        """
        result = []
        for item in tokens:
            result.append(item)
            if item is after:
                result.extend(new_tokens)
        return result

    def insert_before(
        self,
        tokens: List[Union[Token, TokenGroup]],
        before: Union[Token, TokenGroup],
        new_tokens: List[Union[Token, TokenGroup]],
    ) -> List[Union[Token, TokenGroup]]:
        """Insert tokens before a specific token.

        Args:
            tokens: List to modify
            before: Token to insert before
            new_tokens: Tokens to insert

        Returns:
            Modified token list
        """
        result = []
        for item in tokens:
            if item is before:
                result.extend(new_tokens)
            result.append(item)
        return result

    def replace_token(
        self,
        tokens: List[Union[Token, TokenGroup]],
        old: Union[Token, TokenGroup],
        new: Union[Token, TokenGroup, List[Union[Token, TokenGroup]]],
    ) -> List[Union[Token, TokenGroup]]:
        """Replace a token with one or more new tokens.

        Args:
            tokens: List to modify
            old: Token to replace
            new: Replacement token(s)

        Returns:
            Modified token list
        """
        result = []
        new_list = new if isinstance(new, list) else [new]
        for item in tokens:
            if item is old:
                result.extend(new_list)
            else:
                result.append(item)
        return result


def build_config_schema_from_rules(rules: List[BaseRule]) -> Dict[str, ConfigField]:
    """
    Build a configuration schema by introspecting loaded rules.

    Args:
        rules: List of rule instances

    Returns:
        Dict mapping config field names to ConfigField metadata
    """
    schema = {}
    for rule in rules:
        if hasattr(rule, "config_fields") and rule.config_fields:
            for field_name, field_meta in rule.config_fields.items():
                if field_name not in schema:
                    schema[field_name] = field_meta
                # If same field declared multiple times, first one wins
    return schema


def generate_config_defaults(rules: List[BaseRule], dialect: str) -> Dict[str, Any]:
    """
    Generate default configuration values based on loaded rules and dialect.

    Creates a nested structure with 'tidy' and 'rewrite' sections based on
    each rule's rule_type.

    Args:
        rules: List of rule instances
        dialect: Target SQL dialect

    Returns:
        Dict with 'dialect', 'tidy', and 'rewrite' sections
    """
    config_values = {"dialect": dialect, "tidy": {}, "rewrite": {}}
    schema = build_config_schema_from_rules(rules)

    for field_name, field_meta in schema.items():
        # Determine value (dialect-specific or default)
        if field_meta.dialect_defaults and dialect in field_meta.dialect_defaults:
            value = field_meta.dialect_defaults[dialect]
        else:
            value = field_meta.default

        # Find the rule that owns this config field to determine section
        section = None
        for rule in rules:
            if hasattr(rule, "config_fields"):
                # config_fields can be a dict or list
                if isinstance(rule.config_fields, dict):
                    if field_name in rule.config_fields:
                        section = rule.rule_type  # 'tidy' or 'rewrite'
                        break
                elif isinstance(rule.config_fields, list):
                    for cfg_field in rule.config_fields:
                        if hasattr(cfg_field, "name") and cfg_field.name == field_name:
                            section = rule.rule_type
                            break
            if section:
                break

        # Place in appropriate section
        if section == "tidy":
            config_values["tidy"][field_name] = value
        elif section == "rewrite":
            config_values["rewrite"][field_name] = value
        else:
            # Fallback: put in tidy if rule_type not found
            config_values["tidy"][field_name] = value

    return config_values


def get_config_descriptions(rules: List[BaseRule]) -> Dict[str, str]:
    """
    Extract configuration field descriptions from loaded rules.

    Args:
        rules: List of rule instances

    Returns:
        Dict mapping config field names to descriptions
    """
    schema = build_config_schema_from_rules(rules)
    return {name: field.description for name, field in schema.items()}
