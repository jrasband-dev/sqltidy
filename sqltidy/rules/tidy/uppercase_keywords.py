from ..base import BaseRule

SQL_KEYWORDS = {
    "select","from","where","join","on","inner","left","right",
    "full","outer","cross","group","order","by","union","all",
    "distinct","insert","update","delete","top","with","as"
}


class UppercaseKeywordsRule(BaseRule):
    rule_type = "tidy"
    order = 10
    
    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "uppercase_keywords", False):
            return tokens
        return [t.upper() if t.lower() in SQL_KEYWORDS else t for t in tokens]
