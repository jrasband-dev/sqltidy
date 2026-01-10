import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from .base import BaseRule


def _ensure_package_in_sys_modules(package_name):
    """Ensure a package and all parent packages are in sys.modules."""
    if package_name in sys.modules:
        return

    parts = package_name.split(".")
    for i in range(len(parts)):
        partial = ".".join(parts[: i + 1])
        if partial not in sys.modules:
            mod = ModuleType(partial)
            mod.__path__ = []
            sys.modules[partial] = mod


def _load_rule_module(module_name: str):
    """Import a module and instantiate BaseRule subclasses."""
    mod = importlib.import_module(module_name)
    rules = []
    for attr in dir(mod):
        cls = getattr(mod, attr)
        if isinstance(cls, type) and issubclass(cls, BaseRule) and cls != BaseRule:
            rules.append(cls())
    return rules


def _load_plugin_modules(plugin_dir: Path):
    rules = []
    if not plugin_dir.exists():
        return rules
    _ensure_package_in_sys_modules("sqltidy.rules.plugins")
    for file in plugin_dir.glob("*.py"):
        if file.name.startswith("_"):
            continue
        module_name = f"sqltidy.rules.plugins.{file.stem}"
        spec = importlib.util.spec_from_file_location(module_name, file)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = mod
        spec.loader.exec_module(mod)
        for attr in dir(mod):
            cls = getattr(mod, attr)
            if isinstance(cls, type) and issubclass(cls, BaseRule) and cls != BaseRule:
                rules.append(cls())
    return rules


def load_rules(rule_type=None):
    """Load all rules from dialect modules and plugins.

    Args:
        rule_type (str, optional): Filter rules by type ('tidy' or 'rewrite').
                                   None loads all rules.
    """
    rules = []
    rules_dir = Path(__file__).parent

    # Core dialect modules (one file per dialect/general)
    module_files = [
        f
        for f in rules_dir.glob("*.py")
        if f.stem not in {"__init__", "base", "loader"}
    ]
    for file in module_files:
        module_name = f"sqltidy.rules.{file.stem}"
        rules.extend(_load_rule_module(module_name))

    # Load plugin rules from rules/plugins/
    plugin_dir = rules_dir / "plugins"
    rules.extend(_load_plugin_modules(plugin_dir))

    # Filter by rule_type if provided
    if rule_type is not None:
        rules = [r for r in rules if getattr(r, "rule_type", None) == rule_type]

    # Sort by order
    rules.sort(key=lambda r: getattr(r, "order", 100))
    return rules
