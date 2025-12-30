import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from .base import BaseRule


def _ensure_package_in_sys_modules(package_name):
    """Ensure a package and all parent packages are in sys.modules."""
    if package_name in sys.modules:
        return
    
    parts = package_name.split('.')
    for i in range(len(parts)):
        partial = '.'.join(parts[:i+1])
        if partial not in sys.modules:
            mod = ModuleType(partial)
            mod.__path__ = []
            sys.modules[partial] = mod


def _load_modules_from_directory(dir_path, package_prefix):
    """Helper to load all rule modules from a directory."""
    rules = []
    
    if not dir_path.exists():
        return rules
    
    # Ensure the package hierarchy exists
    _ensure_package_in_sys_modules(package_prefix)
    
    for file in dir_path.glob("*.py"):
        if file.name.startswith("_"):
            continue
        
        module_name = f"{package_prefix}.{file.stem}"
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


def load_rules():
    """Load all rules from tidy/ and rewrite/ directories, plus any plugins."""
    rules = []
    rules_dir = Path(__file__).parent

    # Load tidy rules
    tidy_dir = rules_dir / "tidy"
    rules.extend(_load_modules_from_directory(tidy_dir, "sqltidy.rules.tidy"))

    # Load rewrite rules
    rewrite_dir = rules_dir / "rewrite"
    rules.extend(_load_modules_from_directory(rewrite_dir, "sqltidy.rules.rewrite"))

    # Load plugin rules from rules/plugins/
    plugin_dir = rules_dir / "plugins"
    if plugin_dir.exists():
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

    # Sort by order
    rules.sort(key=lambda r: getattr(r, "order", 100))
    return rules
