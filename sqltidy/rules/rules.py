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
        if not getattr(ctx.config, "uppercase_keywords", False):
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



class NewlineAfterSelectRule(BaseRule):
    rule_type = "tidy"
    order = 15
    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "newline_after_select", False):
            return tokens

        sql = "".join(tokens)

        # Replace each SELECT ... FROM block independently to avoid cross-replacement
        pattern = re.compile(r"SELECT\s+(.*?)\s+FROM", flags=re.IGNORECASE | re.DOTALL)

        def _format_match(m):
            cols = m.group(1)
            col_list = [c.strip() for c in cols.split(",")]
            formatted_cols = "\n" + ",\n".join(col_list) + "\n"
            return "SELECT" + formatted_cols + "FROM"

        new_sql = pattern.sub(_format_match, sql)

        # Re-tokenize the modified SQL
        from ..tokenizer import tokenize
        return tokenize(new_sql)

class LeadingCommasRule(BaseRule):
    """
    If ctx.config.leading_commas is True → leading commas:
        SELECT
            a
            ,b
            ,c
    If False → trailing commas (default):
        SELECT
            a,
            b,
            c
    """
    rule_type = "tidy"
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
                    out_tokens.append(",")

                    # Continue without advancing i (we're now at the next real token)
                    continue
            
            out_tokens.append(t)
            i += 1
        
        return out_tokens


class IndentSelectColumnsRule(BaseRule):
    """
    Add 4 spaces of indentation to each selected column.
    This rule should run after NewlineAfterSelectRule and LeadingCommasRule.
    """
    rule_type = "tidy"
    order = 50

    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "indent_select_columns", False):
            return tokens

        # Work with tokens directly - add 4 spaces after each newline in SELECT...FROM blocks
        out_tokens = []
        i = 0
        in_select = False
        
        while i < len(tokens):
            t = tokens[i]
            
            # Detect SELECT keyword
            if t.upper() == "SELECT":
                in_select = True
                out_tokens.append(t)
                i += 1
                continue
            
            # Detect FROM keyword - end of column list
            if t.upper() == "FROM" and in_select:
                in_select = False
                # Remove trailing spaces before FROM
                while out_tokens and out_tokens[-1] == "    ":
                    out_tokens.pop()
                out_tokens.append(t)
                i += 1
                continue
            
            # If we're in SELECT block and hit a newline, add 4 spaces after it
            if in_select and t == "\n":
                out_tokens.append(t)
                i += 1
                # Add 4 spaces after the newline
                out_tokens.append("    ")
                continue
            
            out_tokens.append(t)
            i += 1
        
        return out_tokens


# ========================
# REWRITE RULES
# ========================
# Rules that restructure/reformat SQL


class SubqueryToCTERule(BaseRule):
    rule_type = "rewrite"
    order = 5

    def apply(self, tokens, ctx):
        if not getattr(ctx.config, "enable_subquery_to_cte", False):
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

            # Build CTE block with leading commas for subsequent CTEs:
            # WITH cte_1 AS (...)
            # ,cte_2 AS (...)
            if not ctes:
                return tokens
            cte_block = "WITH " + ctes[0] + "\n"
            if len(ctes) > 1:
                cte_block += "".join(["\n," + c for c in ctes[1:]]) + "\n"

        result_sql = cte_block + sql
        
        # Re-tokenize the modified SQL
        from ..tokenizer import tokenize
        return tokenize(result_sql)




# -------------------------
# Rule loader (auto-load plugins)
# -------------------------

def load_rules():
    rules = [SubqueryToCTERule(), UppercaseKeywordsRule(), NewlineAfterSelectRule(), CompactWhitespaceRule(), LeadingCommasRule(), IndentSelectColumnsRule()]

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
