# sqltidy/rules/rules.py
from .base import BaseRule
import re
import importlib.util
import sys
from pathlib import Path

SQL_KEYWORDS = {
    "select","from","where","join","on","inner","left","right",
    "full","outer","cross","group","order","by","union","all",
    "distinct","insert","update","delete","top","with","as"
}

# ========================
# TIDY RULES
# ========================
# Rules that format/clean up SQL without changing structure

class UppercaseKeywordsRule(BaseRule):
    rule_type = "tidy"
    order = 10
    def apply(self, tokens, ctx):
        if not ctx.config.uppercase_keywords:
            return tokens
        return [t.upper() if t.lower() in SQL_KEYWORDS else t for t in tokens]

class CompactWhitespaceRule(BaseRule):
    rule_type = "tidy"
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


# ========================
# REWRITE RULES
# ========================
# Rules that restructure/reformat SQL

class NewlineAfterSelectRule(BaseRule):
    rule_type = "rewrite"
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

        # Re-tokenize the modified SQL
        from ..tokenizer import tokenize
        return tokenize(sql)

class LeadingCommasRule(BaseRule):
    """
    If ctx.config.leading_commas is True → leading commas:
        SELECT
            a
          , b
          , c
    If False → trailing commas (default):
        SELECT
            a,
            b,
            c
    """
    rule_type = "rewrite"
    order = 45

    def apply(self, tokens, ctx):
        leading = getattr(ctx.config, "leading_commas", False)
        
        if not leading:
            # Default behavior is trailing commas, which is what NewlineAfterSelectRule produces
            return tokens
        
        # For leading commas, we need to move commas after the preceding newline+space
        # to before the next token (on the same line as the previous value, but after newline+indent)
        out_tokens = []
        i = 0
        
        while i < len(tokens):
            t = tokens[i]
            
            # When we hit a comma, look ahead to see if it's followed by newline+space(s)+next_token
            if t == "," and i + 1 < len(tokens):
                # Check if next is space/newline
                if tokens[i + 1] in (" ", "\n"):
                    # Skip the comma for now, we'll add it later
                    i += 1
                    # Collect the whitespace/newline
                    whitespace = []
                    while i < len(tokens) and tokens[i] in (" ", "\n"):
                        whitespace.append(tokens[i])
                        i += 1
                    
                    # Now we're at the next token, insert: newline + "  " + comma + space
                    out_tokens.append("\n")
                    out_tokens.append("  ")  # 2-space indent for leading comma
                    out_tokens.append(",")
                    out_tokens.append(" ")
                    
                    # Continue without advancing i (we're now at the next real token)
                    continue
            
            out_tokens.append(t)
            i += 1
        
        return out_tokens




class SubqueryToCTERule(BaseRule):
    rule_type = "rewrite"
    order = 5

    def apply(self, tokens, ctx):
        if not ctx.config.enable_subquery_to_cte:
            return tokens

        # Convert tokens back to SQL string
        sql = "".join(tokens)
        
        # VERY naive example implementation:
        pattern = r"\(\s*SELECT(.*?)\)"
        matches = re.findall(pattern, sql, flags=re.IGNORECASE | re.DOTALL)
        if not matches:
            return tokens

        ctes = []
        i = 1
        for subquery in matches:
            ctename = f"cte_{i}"
            cte_sql = f"{ctename} AS (\nSELECT{subquery}\n)"
            ctes.append(cte_sql)
            sql = re.sub(
                r"\(\s*SELECT" + re.escape(subquery) + r"\)",
                ctename,
                sql,
                flags=re.IGNORECASE | re.DOTALL,
                count=1
            )
            i += 1

        cte_block = "WITH " + ",\n".join(ctes) + "\n"
        result_sql = cte_block + sql
        
        # Re-tokenize the modified SQL
        from ..tokenizer import tokenize
        return tokenize(result_sql)




# -------------------------
# Rule loader (auto-load plugins)
# -------------------------

def load_rules():
    rules = [SubqueryToCTERule(), UppercaseKeywordsRule(), NewlineAfterSelectRule(), CompactWhitespaceRule(), LeadingCommasRule()]

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
