from typing import List, Optional, Set, Dict, Any
from dataclasses import dataclass
from ..rulebook import SQLTidyConfig


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


class BaseRule:
    """
    Base class for all SQL formatting rules.
    
    Rules can be either 'tidy' (formatting without structural changes) or 
    'rewrite' (transformations that change SQL structure).
    
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
        supported_dialects (Optional[Set[str]]): Dialects this rule supports (None = all)
        config_fields (Optional[Dict[str, ConfigField]]): Configuration fields this rule uses
    """
    order: int = 100
    rule_type: Optional[str] = None  # "tidy" or "rewrite"
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
    
    def apply(self, tokens: List[str], ctx: FormatterContext) -> List[str]:
        """
        Apply the rule to the token list.
        
        This is the main entry point. Override this in subclasses.
        
        Args:
            tokens: List of SQL tokens
            ctx: Formatter context containing configuration
            
        Returns:
            Modified list of tokens
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement apply() method"
        )


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
        if hasattr(rule, 'config_fields') and rule.config_fields:
            for field_name, field_meta in rule.config_fields.items():
                if field_name not in schema:
                    schema[field_name] = field_meta
                # If same field declared multiple times, first one wins
    return schema


def generate_config_defaults(rules: List[BaseRule], dialect: str) -> Dict[str, Any]:
    """
    Generate default configuration values based on loaded rules and dialect.
    
    Args:
        rules: List of rule instances
        dialect: Target SQL dialect
        
    Returns:
        Dict of config field names to default values
    """
    config_values = {'dialect': dialect}
    schema = build_config_schema_from_rules(rules)
    
    for field_name, field_meta in schema.items():
        # Check for dialect-specific default first
        if field_meta.dialect_defaults and dialect in field_meta.dialect_defaults:
            config_values[field_name] = field_meta.dialect_defaults[dialect]
        else:
            config_values[field_name] = field_meta.default
    
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
