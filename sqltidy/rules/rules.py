# sqltidy/rules/rules.py
from .base import BaseRule, FormatterContext
import re
import importlib.util
import sys
from pathlib import Path

SQL_KEYWORDS = {
    "select","from","where","join","on","inner","left","right",
    "full","outer","cross","group","order","by","union","all",
    "distinct","insert","update","delete","top","with","as"
}

# -------------------------
# Built-in rules
# -------------------------

class UppercaseKeywordsRule(BaseRule):
    order = 10
    def apply(self, tokens, ctx):
        if not ctx.config.uppercase_keywords:
            return tokens
        return [t.upper() if t.lower() in SQL_KEYWORDS else t for t in tokens]

class NewlineAfterSelectRule(BaseRule):
    order = 15
    def apply(self, tokens, ctx):
        if not ctx.config.newline_after_select:
            return tokens

        sql = "".join(tokens)
        pattern = r"SELECT\s+(.*?)\s+FROM"
        matches = re.findall(pattern, sql, flags=re.IGNORECASE | re.DOTALL)

        if not matches:
            return tokens

        for cols in matches:
            col_list = [c.strip() for c in cols.split(",")]
            formatted_cols = "\n    " + ",\n    ".join(col_list) + "\n"
            new_block = "SELECT" + formatted_cols + "FROM"
            sql = re.sub(pattern, new_block, sql, flags=re.IGNORECASE | re.DOTALL)

        return list(sql)

class CompactWhitespaceRule(BaseRule):
    order = 20
    def apply(self, tokens, ctx):
        out = []
        prev = None
        for t in tokens:
            if t == " " and prev == " ":
                continue
            out.append(t)
            prev = t
        return out

# -------------------------
# Rule loader (auto-load plugins)
# -------------------------

def load_rules():
    rules = [UppercaseKeywordsRule(), NewlineAfterSelectRule(), CompactWhitespaceRule()]

    # load plugin rules from rules/plugins/
    plugin_dir = Path(__file__).parent / "plugins"
    if plugin_dir.exists():
        for file in plugin_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            spec = importlib.util.spec_from_file_location(file.stem, file)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[file.stem] = mod
            spec.loader.exec_module(mod)
            for attr in dir(mod):
                cls = getattr(mod, attr)
                if isinstance(cls, type) and issubclass(cls, BaseRule) and cls != BaseRule:
                    rules.append(cls())

    # sort by order
    rules.sort(key=lambda r: getattr(r, "order", 100))
    return rules
