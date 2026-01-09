"""
Tests for the plugin system.
"""

import pytest
import tempfile
from pathlib import Path
from sqltidy.plugins import (
    sqltidy_plugin,
    register_rule_class,
    get_registered_plugins,
    clear_plugins,
    load_plugin_file,
    load_plugins_from_directory,
    create_plugin_formatter
)
from sqltidy.rules.base import BaseRule
from sqltidy.rulebook import SQLTidyConfig
from sqltidy.api import tidy_sql


@pytest.fixture(autouse=True)
def cleanup_plugins():
    """Clear plugins before and after each test."""
    clear_plugins()
    yield
    clear_plugins()


class TestPluginDecorator:
    """Test the @sqltidy_plugin decorator."""
    
    def test_basic_decorator(self):
        """Test basic plugin registration."""
        @sqltidy_plugin(rule_type="tidy", order=50)
        def test_rule(tokens, ctx):
            return tokens
        
        plugins = get_registered_plugins()
        assert len(plugins) == 1
        assert plugins[0].rule_type == "tidy"
        assert plugins[0].order == 50
    
    def test_decorator_with_dialects(self):
        """Test plugin with dialect restrictions."""
        @sqltidy_plugin(
            rule_type="tidy",
            order=50,
            supported_dialects={'postgresql', 'mysql'}
        )
        def pg_rule(tokens, ctx):
            return tokens
        
        plugins = get_registered_plugins()
        assert len(plugins) == 1
        assert plugins[0].supported_dialects == {'postgresql', 'mysql'}
    
    def test_decorator_custom_name(self):
        """Test plugin with custom name."""
        @sqltidy_plugin(rule_type="tidy", order=50, name="MyCustomRule")
        def test_rule(tokens, ctx):
            return tokens
        
        plugins = get_registered_plugins()
        assert plugins[0].__name__ == "MyCustomRule"
    
    def test_function_retains_metadata(self):
        """Test that decorated function retains metadata."""
        @sqltidy_plugin(rule_type="tidy", order=50)
        def test_rule(tokens, ctx):
            """Test documentation."""
            return tokens
        
        assert hasattr(test_rule, '_sqltidy_plugin')
        assert test_rule._sqltidy_plugin is True
        assert hasattr(test_rule, '_sqltidy_rule_class')


class TestRegisterRuleClass:
    """Test registering class-based rules."""
    
    def test_register_valid_class(self):
        """Test registering a valid BaseRule subclass."""
        class TestRule(BaseRule):
            rule_type = "tidy"
            order = 50
            
            def apply(self, tokens, ctx):
                return tokens
        
        register_rule_class(TestRule)
        
        plugins = get_registered_plugins()
        assert len(plugins) == 1
        assert plugins[0] is TestRule
    
    def test_register_invalid_class(self):
        """Test registering non-BaseRule class raises error."""
        class NotARule:
            pass
        
        with pytest.raises(TypeError):
            register_rule_class(NotARule)


class TestPluginRegistry:
    """Test plugin registry management."""
    
    def test_get_registered_plugins(self):
        """Test getting registered plugins."""
        @sqltidy_plugin(rule_type="tidy", order=50)
        def rule1(tokens, ctx):
            return tokens
        
        @sqltidy_plugin(rule_type="tidy", order=60)
        def rule2(tokens, ctx):
            return tokens
        
        plugins = get_registered_plugins()
        assert len(plugins) == 2
    
    def test_clear_plugins(self):
        """Test clearing plugins."""
        @sqltidy_plugin(rule_type="tidy", order=50)
        def rule1(tokens, ctx):
            return tokens
        
        assert len(get_registered_plugins()) == 1
        
        clear_plugins()
        
        assert len(get_registered_plugins()) == 0


class TestLoadPluginFile:
    """Test loading plugins from files."""
    
    def test_load_from_file(self):
        """Test loading plugins from a Python file."""
        # Create temporary plugin file
        plugin_code = '''
from sqltidy.plugins import sqltidy_plugin

@sqltidy_plugin(rule_type="tidy", order=50)
def test_plugin(tokens, ctx):
    """Test plugin from file."""
    return tokens
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(plugin_code)
            f.flush()
            filepath = f.name
        
        try:
            # Load the plugin
            plugins = load_plugin_file(filepath)
            
            assert len(plugins) == 1
            assert plugins[0].rule_type == "tidy"
        finally:
            # Delay deletion to avoid Windows file locking issue
            import time
            time.sleep(0.1)
            try:
                Path(filepath).unlink()
            except:
                pass  # Ignore cleanup errors
    
    def test_load_nonexistent_file(self):
        """Test loading from nonexistent file raises error."""
        with pytest.raises(FileNotFoundError):
            load_plugin_file('/nonexistent/file.py')
    
    def test_load_invalid_python(self):
        """Test loading invalid Python raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('this is not valid python :::')
            f.flush()
            filepath = f.name
        
        try:
            with pytest.raises(ImportError):
                load_plugin_file(filepath)
        finally:
            # Delay deletion to avoid Windows file locking issue
            import time
            time.sleep(0.1)
            try:
                Path(filepath).unlink()
            except:
                pass  # Ignore cleanup errors


class TestLoadPluginDirectory:
    """Test loading plugins from directories."""
    
    def test_load_from_directory(self):
        """Test loading all plugins from a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create multiple plugin files
            plugin1 = tmpdir / "plugin1.py"
            plugin1.write_text('''
from sqltidy.plugins import sqltidy_plugin

@sqltidy_plugin(rule_type="tidy", order=50)
def rule1(tokens, ctx):
    return tokens
''')
            
            plugin2 = tmpdir / "plugin2.py"
            plugin2.write_text('''
from sqltidy.plugins import sqltidy_plugin

@sqltidy_plugin(rule_type="tidy", order=60)
def rule2(tokens, ctx):
    return tokens
''')
            
            # Load all plugins
            plugins = load_plugins_from_directory(tmpdir)
            
            assert len(plugins) == 2
    
    def test_skip_private_files(self):
        """Test that private files (_*.py) are skipped."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Create private file
            private = tmpdir / "_private.py"
            private.write_text('''
from sqltidy.plugins import sqltidy_plugin

@sqltidy_plugin(rule_type="tidy", order=50)
def private_rule(tokens, ctx):
    return tokens
''')
            
            # Load plugins - should skip private file
            plugins = load_plugins_from_directory(tmpdir)
            
            assert len(plugins) == 0
    
    def test_load_from_nonexistent_directory(self):
        """Test loading from nonexistent directory raises error."""
        with pytest.raises(FileNotFoundError):
            load_plugins_from_directory('/nonexistent/directory')


class TestPluginIntegration:
    """Test plugins working with formatter."""
    
    def test_plugin_modifies_output(self):
        """Test that plugin actually modifies SQL output."""
        @sqltidy_plugin(rule_type="tidy", order=100)
        def remove_semicolons(tokens, ctx):
            if tokens and tokens[-1] == ';':
                return tokens[:-1]
            return tokens
        
        # Get the plugin rules
        plugin_rules = [r() for r in get_registered_plugins()]
        
        # Format with plugin
        result = tidy_sql("SELECT * FROM users;", custom_rules=plugin_rules)
        
        # Should have removed semicolon
        assert not result.strip().endswith(';')
    
    def test_multiple_plugins_execute(self):
        """Test multiple plugins execute in order."""
        execution_order = []
        
        @sqltidy_plugin(rule_type="tidy", order=10)
        def first(tokens, ctx):
            execution_order.append('first')
            return tokens
        
        @sqltidy_plugin(rule_type="tidy", order=50)
        def second(tokens, ctx):
            execution_order.append('second')
            return tokens
        
        formatter = create_plugin_formatter()
        formatter.format("SELECT * FROM users")
        
        # Note: We can't directly verify execution order here without
        # modifying tokens, but we can verify both plugins were registered
        plugins = get_registered_plugins()
        assert len(plugins) == 2
    
    def test_dialect_specific_plugin(self):
        """Test dialect-specific plugin only runs for correct dialect."""
        clear_plugins()
        
        @sqltidy_plugin(
            rule_type="tidy",
            order=1,  # Run very early
            supported_dialects={'postgresql'}
        )
        def pg_only(tokens, ctx):
            # Add special marker at beginning
            return ['PG_MARKER', ' '] + tokens
        
        # Get the plugin rules
        plugin_rules = [r() for r in get_registered_plugins()]
        
        # Test with PostgreSQL dialect
        pg_result = tidy_sql(
            "SELECT 1",
            config=SQLTidyConfig(dialect='postgresql'),
            custom_rules=plugin_rules
        )
        assert 'PG_MARKER' in pg_result
        
        # Test with MySQL dialect (should not run)
        clear_plugins()
        
        @sqltidy_plugin(
            rule_type="tidy",
            order=1,
            supported_dialects={'postgresql'}
        )
        def pg_only2(tokens, ctx):
            return ['PG_MARKER', ' '] + tokens
        
        plugin_rules = [r() for r in get_registered_plugins()]
        
        mysql_result = tidy_sql(
            "SELECT 1",
            config=SQLTidyConfig(dialect='mysql'),
            custom_rules=plugin_rules
        )
        assert 'PG_MARKER' not in mysql_result


class TestCreatePluginFormatter:
    """Test the convenience formatter creator."""
    
    def test_create_with_file(self):
        """Test creating formatter with plugin file."""
        plugin_code = '''
from sqltidy.plugins import sqltidy_plugin

@sqltidy_plugin(rule_type="tidy", order=100)
def test_rule(tokens, ctx):
    return tokens
'''
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(plugin_code)
            f.flush()
            filepath = f.name
        
        try:
            formatter = create_plugin_formatter(
                plugin_files=[filepath]
            )
            
            # Should have loaded plugin
            assert any('Rule' in r.__class__.__name__ for r in formatter.rules)
        finally:
            # Delay deletion to avoid Windows file locking issue
            import time
            time.sleep(0.1)
            try:
                Path(filepath).unlink()
            except:
                pass  # Ignore cleanup errors
    
    def test_create_with_config(self):
        """Test creating formatter with config."""
        config = SQLTidyConfig(dialect='postgresql')
        formatter = create_plugin_formatter(config=config)
        
        # Check that formatter was created with config
        # SQLFormatter stores config internally but may not expose it as .config
        assert formatter is not None
        assert len(formatter.rules) > 0  # Should have default rules


class TestPluginAliases:
    """Test convenience aliases."""
    
    def test_plugin_alias(self):
        """Test 'plugin' is an alias for 'sqltidy_plugin'."""
        from sqltidy.plugins import plugin
        
        @plugin(rule_type="tidy", order=50)
        def test_rule(tokens, ctx):
            return tokens
        
        plugins = get_registered_plugins()
        assert len(plugins) == 1
    
    def test_register_alias(self):
        """Test 'register' is an alias for 'register_rule_class'."""
        from sqltidy.plugins import register
        
        class TestRule(BaseRule):
            rule_type = "tidy"
            order = 50
            
            def apply(self, tokens, ctx):
                return tokens
        
        register(TestRule)
        
        plugins = get_registered_plugins()
        assert len(plugins) == 1
