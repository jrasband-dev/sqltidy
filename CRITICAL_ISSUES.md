# Critical Issues Requiring Immediate Attention

This document lists the most critical issues found during the repository scan that should be addressed as soon as possible.

## 1. Test Import Failure ❌ BLOCKING

**File:** `tests/unit/test_custom_rules.py`  
**Line:** 8  
**Severity:** CRITICAL  

**Issue:**
```python
from sqltidy.rules.helpers import (
    create_simple_rule,
    create_token_replacement_rule,
    create_pattern_rule,
    create_keyword_wrapper_rule,
    create_filter_rule,
    create_transform_rule,
    remove_trailing_semicolons,
    add_newline_before_keyword,
    replace_token,
    uppercase_keywords,
)
```

**Error:** `ModuleNotFoundError: No module named 'sqltidy.rules.helpers'`

**Impact:** This prevents ALL unit tests from running. Test collection fails immediately.

**Possible Solutions:**
1. Create the missing `sqltidy/rules/helpers.py` module with the expected functions
2. Delete or update `tests/unit/test_custom_rules.py` if the helpers are no longer needed
3. Update the imports to use the correct module path

---

## 2. Function Redefinition ⚠️ HIGH

**File:** `sqltidy/tokenizer.py`  
**Lines:** 118, 241  
**Severity:** HIGH  

**Issue:** The function `get_token_type` is defined twice in the same file.

**Line 118:**
```python
def get_token_type(value: str, dialect: Union[str, SQLDialect] = 'sqlserver') -> TokenType:
    # First definition
```

**Line 241:**
```python
def get_token_type(value: str, dialect: Union[str, SQLDialect] = 'sqlserver') -> TokenType:
    # Second definition - OVERWRITES THE FIRST!
```

**Impact:** 
- The second definition completely overrides the first
- Code calling the function will only get the second implementation
- The first implementation is dead code
- Confusing for developers and code reviewers

**Detection:**
- Flake8: F811 (redefinition of unused 'get_token_type')
- Mypy: error: Name "get_token_type" already defined on line 118

**Solution:** Remove one of the definitions or rename if they serve different purposes.

---

## 3. Type Safety Issues 🔧 MEDIUM-HIGH

### Issue 3a: Missing Type Annotations

**File:** `sqltidy/tokenizer.py`  
**Line:** 314  
**Code:** `result = []`

**Error:** Need type annotation for "result" (hint: "result: list[<type>] = ...")

**Impact:** Reduces type safety and IDE support.

---

**File:** `sqltidy/tokenizer.py`  
**Line:** 440  
**Code:** `current_clause = []`

**Error:** Need type annotation for "current_clause"

---

### Issue 3b: Incompatible Type Defaults

**File:** `sqltidy/core.py`  
**Line:** 10  

**Error:** 
- Incompatible default for argument "config" (default has type "None", argument has type "SQLTidyConfig")
- Incompatible default for argument "rule_type" (default has type "None", argument has type "str")

**Issue:** PEP 484 prohibits implicit Optional. The function signature likely looks like:
```python
def some_function(config: SQLTidyConfig = None, rule_type: str = None):
    ...
```

**Should be:**
```python
from typing import Optional

def some_function(config: Optional[SQLTidyConfig] = None, rule_type: Optional[str] = None):
    ...
```

---

## 4. Platform Compatibility Issue 🔧 MEDIUM

**File:** `sqltidy/generator.py`  
**Line:** 422  
**Severity:** MEDIUM  

**Code:**
```python
if os.name == 'nt':  # Windows
    os.startfile(user_config_file)
elif os.name == 'posix':  # macOS and Linux
    opener = "open" if os.uname().sysname == "Darwin" else "xdg-open"
    subprocess.run([opener, str(user_config_file)])
```

**Issues:**
1. **Mypy Error:** Module has no attribute "startfile" 
   - `os.startfile` only exists on Windows, causing type checker to fail on Linux
2. **Missing Error Handling:** No try-except around `subprocess.run()`
3. **Return Code Ignored:** subprocess.run() doesn't check if the command succeeded

**Solution:**
```python
if os.name == 'nt':  # Windows
    if hasattr(os, 'startfile'):
        os.startfile(user_config_file)  # type: ignore[attr-defined]
    else:
        print("os.startfile not available on this platform")
elif os.name == 'posix':  # macOS and Linux
    opener = "open" if os.uname().sysname == "Darwin" else "xdg-open"
    try:
        subprocess.run([opener, str(user_config_file)], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to open config file: {e}")
```

---

## 5. Unused Imports 🔧 MEDIUM

**File:** `sqltidy/rules/tidy/uppercase_keywords.py`  
**Line:** 1  

**Code:** `from typing import Optional`

**Error:** F401 'typing.Optional' imported but unused

**Impact:** Clutters code, can cause confusion

**Solution:** Remove the unused import

---

## 6. Union Type Attribute Access ⚠️ MEDIUM

**File:** `sqltidy/tokenizer.py`  
**Lines:** 327, 329  

**Error:** Item "TokenGroup" of "Token | TokenGroup" has no attribute "value"

**Issue:** Code is accessing `.value` on a union type without checking which type it is first.

**Solution:** Add type checking before attribute access:
```python
if isinstance(obj, Token):
    value = obj.value
elif isinstance(obj, TokenGroup):
    # Handle TokenGroup differently
    pass
```

---

## Priority Order for Fixes

### P0 - Must Fix (Blocks Development)
1. ✅ **Fix test import error** - Tests cannot run at all

### P1 - Should Fix Soon (Correctness Issues)
2. ✅ **Remove function redefinition** - Causes unexpected behavior
3. ✅ **Fix union type attribute access** - Potential runtime errors

### P2 - Should Fix (Quality Issues)
4. 📝 **Add explicit Optional types** - Better type safety
5. 📝 **Fix platform compatibility** - Cross-platform issues
6. 📝 **Add missing type annotations** - Improves maintainability

### P3 - Nice to Have
7. 🔧 **Remove unused imports** - Code cleanliness

---

## Automated Fix Commands

For some issues, automated fixes are possible:

### Remove Unused Imports
```bash
autoflake --in-place --remove-all-unused-imports sqltidy/**/*.py
```

### Fix Trailing Whitespace
```bash
find sqltidy -name "*.py" -exec sed -i 's/[[:space:]]*$//' {} +
```

### Format with Black (if desired)
```bash
black sqltidy
```

---

## Testing After Fixes

After fixing critical issues, run:

```bash
# Run tests
python -m pytest tests/ -v

# Check types
mypy sqltidy

# Check style
flake8 sqltidy

# Check code quality
pylint sqltidy

# Check security
bandit -r sqltidy
```

---

## Estimated Effort

| Issue | Estimated Time | Risk Level |
|-------|---------------|------------|
| Test import error | 30 min - 2 hours | Medium (depends on whether to create or delete) |
| Function redefinition | 15 minutes | Low |
| Type annotations | 1-2 hours | Low |
| Platform compatibility | 30 minutes | Low |
| Union type fixes | 1 hour | Medium |
| Unused imports | 15 minutes | Low |

**Total Estimated Effort:** 3.5 - 6 hours

---

*This report was generated on 2026-01-02 by automated code scanning tools.*
