from typing import List, Optional, Set
from ..config import SQLTidyConfig


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
    
    Attributes:
        order (int): Execution order (lower numbers run first)
        rule_type (str): Either "tidy" or "rewrite"
        supported_dialects (Optional[Set[str]]): Dialects this rule supports (None = all)
    """
    order: int = 100
    rule_type: Optional[str] = None  # "tidy" or "rewrite"
    supported_dialects: Optional[Set[str]] = None  # None = all dialects
    
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
