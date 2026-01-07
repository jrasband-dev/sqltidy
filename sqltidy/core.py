# sqltidy/core.py
import re
from typing import List, Dict, Any
from .rulebook import SQLTidyConfig
from .tokenizer import TOKEN_RE

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

    def tokenize(self, sql: str) -> List[str]:
        """Convert raw SQL into proper tokens without external dependencies."""
        tokens = []
        for groups in TOKEN_RE.findall(sql):
            # Find the first non-empty capturing group
            for t in groups:
                if t == "":
                    continue
                # normalize whitespace
                if t.isspace():
                    if "\n" in t:
                        tokens.append("\n")
                    else:
                        tokens.append(" ")
                else:
                    tokens.append(t)
                break

        return tokens

    def format(self, sql: str, return_metadata: bool = False) -> Any:
        """Format SQL and optionally return metadata about applied rules.
        
        Args:
            sql: SQL string to format
            return_metadata: If True, return dict with 'sql' and 'applied_rules'
            
        Returns:
            Formatted SQL string, or dict with metadata if return_metadata=True
        """
        tokens = self.tokenize(sql)
        self.applied_rules = []  # Reset for each format call
        all_applicable_rules = []  # Track all rules that could have been applied

        # Apply rules that are applicable to the current dialect
        for rule in sorted(self.rules, key=lambda r: getattr(r, "order", 100)):
            if rule.is_applicable(self.ctx):
                all_applicable_rules.append({
                    'name': rule.__class__.__name__,
                    'type': getattr(rule, 'rule_type', 'unknown'),
                    'order': getattr(rule, 'order', 100)
                })
                
                old_tokens = tokens
                tokens = rule.apply(tokens, self.ctx)
                # Track if rule actually changed anything
                if tokens != old_tokens:
                    self.applied_rules.append({
                        'name': rule.__class__.__name__,
                        'type': getattr(rule, 'rule_type', 'unknown'),
                        'order': getattr(rule, 'order', 100)
                    })

        formatted_sql = self.join_tokens(tokens)
        
        if return_metadata:
            return {
                'sql': formatted_sql,
                'applied_rules': self.applied_rules,
                'all_applicable_rules': all_applicable_rules,
                'total_rules': len(self.rules),
                'applicable_rules': sum(1 for r in self.rules if r.is_applicable(self.ctx))
            }
        
        return formatted_sql

    def join_tokens(self, tokens: List[str]) -> str:
        """Reassemble tokens into formatted SQL text."""
        return "".join(tokens).strip()
