"""
Base classes and infrastructure for the declarative SQL pattern system.

This module provides the core pattern matching framework that other patterns build upon.
"""
from typing import List, Optional, Union, Dict, Any, Pattern, Literal, Iterable
from dataclasses import dataclass



# Import types from tokenizer
# Note: We avoid circular imports by using TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..tokenizer import Token, TokenGroup, GroupType
    from ..dialects.base import SQLDialect
    from ..dialects import get_dialect


@dataclass(frozen=True)
class Construct:
    name: str
    pattern: Pattern
    dialect: Literal['all','sqlserver','postgres','mysql','sqlite','oracle'] = 'all'
    
    def __post_init__(self):
        # Compile regex once
        object.__setattr__(self, "_compiled", self.pattern)

    @property
    def regex(self) -> Pattern:
        return self._compiled

    def matches(self, text: str) -> bool:
        return bool(self.regex.search(text))
    
    def is_applicable(self, dialect) -> bool:
        """Check if this construct is applicable for the given dialect."""
        if self.dialect == 'all':
            return True
        
        # Handle both string and dialect object
        dialect_name = dialect.name if hasattr(dialect, 'name') else str(dialect)
        return self.dialect == dialect_name






def match_constructs(sql: str, dialect: str = "sqlserver", constructs: Optional[List[Construct]] = None) -> List[Dict[str, Any]]:
    """
    Match SQL constructs (patterns) in the given SQL string.
    
    Args:
        sql: SQL string to analyze
        dialect: SQL dialect to use (default: "sqlserver")
        constructs: List of constructs to match. If None, uses all registered constructs.
    
    Returns:
        List of dictionaries containing match information:
        - name: construct name
        - match: regex match object
        - start: start position in SQL string
        - end: end position in SQL string
        - text: matched text
    """
    from ..dialects import get_dialect
    
    if isinstance(dialect, str):
        dialect_obj = get_dialect(dialect)
    else:
        dialect_obj = dialect
    
    # Get constructs to match
    if constructs is None:
        constructs = get_all_constructs(dialect.name if hasattr(dialect, 'name') else dialect)
    
    # Filter constructs by dialect
    dialect_name = dialect_obj.name if hasattr(dialect_obj, 'name') else dialect
    filtered_constructs = [
        c for c in constructs 
        if c.dialect == 'all' or c.dialect == dialect_name
    ]
    
    constructs = []
    for construct in filtered_constructs:
        for match in construct.regex.finditer(sql):
            constructs.append({
                'name': construct.name,
                'match': match,
                'start': match.start(),
                'end': match.end(),
                'text': match.group(0),
                'groups': match.groupdict()
            })
    
    # Sort by start position
    constructs.sort(key=lambda x: x['start'])
    
    return constructs



class ConstructRegistry:
    def __init__(self):
        self._constructs: Dict[str, Construct] = {}

    def register(self, construct: Construct) -> None:
        self._constructs[construct.name] = construct

    def all(self) -> List[Construct]:
        return list(self._constructs.values())
    
    def clear(self) -> None:
        self._constructs.clear()

    def __iter__(self) -> Iterable[Construct]:
        return iter(self._constructs.values())


# Global pattern registry
_global_registry = ConstructRegistry()


def register_construct(construct: Construct):
    """Register a pattern in the global registry."""
    _global_registry.register(construct)


def get_pattern(name: str) -> Optional[Construct]:
    """Get a pattern from the global registry by name."""
    return _global_registry._constructs.get(name)


def get_all_constructs(dialect: Optional[str] = None) -> List[Construct]:
    """Get all patterns from the global registry."""
    return _global_registry.all()

def clear_constructs():
    """Clear the global pattern registry."""
    _global_registry.clear()






__all__ = [
    "Construct",
    "ConstructRegistry",
    "register_construct",
    "get_pattern",
    "get_all_constructs",
    "clear_constructs",
    "match_constructs",
]
