# Default Rules

from dataclasses import dataclass, field

@dataclass
class TidyConfig:
    uppercase_keywords: bool = True
    newline_after_select: bool = True
    compact: bool = True
    leading_commas: bool = True
    indent_select_columns: bool = True



@dataclass
class RewriteConfig:
    enable_subquery_to_cte: bool = True
    enable_alias_style_abc: bool = False
    enable_alias_style_t_numeric: bool = False
