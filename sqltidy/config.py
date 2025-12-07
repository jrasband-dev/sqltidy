# Default Rules

from dataclasses import dataclass

@dataclass
class TidyConfig:
    uppercase_keywords = True
    newline_after_select = True
    compact = True
    leading_commas = False



@dataclass
class RewriteConfig:
    enable_subquery_to_cte = True
