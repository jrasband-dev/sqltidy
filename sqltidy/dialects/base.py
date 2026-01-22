"""
Base class for SQL dialects.

Each dialect defines its own keywords, data types, functions, and syntax rules.
"""

from abc import ABC, abstractmethod
from typing import Set, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ..constructs import Construct
    from ..tokenizer.base import TokenPattern


class SQLDialect(ABC):
    """
    Base class for SQL dialects.

    Each dialect implementation should provide:
    - name: Unique identifier for the dialect
    - keywords: Set of SQL keywords specific to this dialect
    - data_types: Set of data type names
    - functions: Set of built-in function names
    - identifier_chars: Special characters allowed in identifiers (e.g., '@' for SQL Server)
    - quote_chars: Dictionary of quote characters for identifiers and strings
    - comment_styles: List of comment patterns supported
    """

    def __init__(self):
        """Initialize the dialect."""
        self._constructs: List["Construct"] = []
        self._token_patterns: List["TokenPattern"] = []
        self._token_patterns_initialized = False
        self._validate()
        self._register_constructs()

    def _register_constructs(self):
        """
        Register dialect-specific constructs.

        Override this method to register constructs specific to this dialect.
        Constructs are used to identify dialect-specific SQL patterns.

        Base implementation registers common constructs (CTE, WINDOW_FUNCTION, SUBQUERY)
        that are applicable to all dialects.

        Example:
            def _register_constructs(self):
                # First call parent to register common constructs
                super()._register_constructs()

                # Then register dialect-specific constructs
                from ..constructs.base import Construct
                self.register_construct(TryCatchConstruct())
                self.register_construct(OutputClauseConstruct())
        """
        import re
        from ..constructs.base import Construct

        # Register common constructs applicable to all SQL dialects

        # CTE (Common Table Expression)
        self.register_construct(
            Construct(
                name="CTE",
                type="clause",
                dialect="all",
                pattern=re.compile(
                    r"""
            ^\s*WITH\s+                # WITH keyword at start
            (?P<cte_name>\w+)          # CTE name (identifier)
            (?:\s*\((?P<columns>[^)]*)\))?  # Optional column list
            \s+AS\s*                   # AS keyword
            \(\s*                      # Opening parenthesis for subquery
            (?P<subquery>.*?)          # Subquery (non-greedy)
            \)\s*                      # Closing parenthesis
            """,
                    re.VERBOSE | re.IGNORECASE | re.DOTALL | re.MULTILINE,
                ),
            )
        )

        # Window Function
        self.register_construct(
            Construct(
                name="WindowFunction",
                type="clause",
                dialect="all",
                pattern=re.compile(
                    r"""
            ^(?P<function_name>\w+)\s*     # Function name
            \(\s*(?P<arguments>.*?)\s*\)\s* # Function arguments
            OVER\s*                        # OVER keyword
            \(\s*(?P<over_clause>.*?)\s*\)  # OVER clause content
            """,
                    re.VERBOSE | re.IGNORECASE | re.DOTALL | re.MULTILINE,
                ),
            )
        )

        # Subquery
        self.register_construct(
            Construct(
                name="Subquery",
                type="clause",
                dialect="all",
                pattern=re.compile(
                    r"""
            \(\s*                          # Opening parenthesis
            (?P<select_statement>SELECT\s+.*?) # SELECT statement
            \s*\)\s*                       # Closing parenthesis
            (?:AS\s+(?P<alias>\w+))?       # Optional alias
            """,
                    re.VERBOSE | re.IGNORECASE | re.DOTALL,
                ),
            )
        )

    def _register_token_patterns(self):
        """
        Register dialect-specific token patterns.

        Override this method to register token patterns specific to this dialect.
        Token patterns define how SQL strings are tokenized.

        Example:
            def _register_token_patterns(self):
                import re
                from ..tokenizer.base import TokenPattern
                self.register_token_pattern(TokenPattern('Comment', re.compile(r'--[^\n]*')))
        """
        pass

    def register_construct(self, construct: "Construct"):
        """
        Register a construct for this dialect.

        Args:
            construct: The construct to register
        """
        self._constructs.append(construct)

    def get_constructs(self) -> List["Construct"]:
        """
        Get all constructs registered for this dialect.

        Returns:
            List of Construct objects
        """
        return self._constructs.copy()

    def register_token_pattern(self, pattern: "TokenPattern"):
        """
        Register a token pattern for this dialect.

        Args:
            pattern: The TokenPattern to register
        """
        self._token_patterns.append(pattern)

    def get_token_patterns(self) -> List["TokenPattern"]:
        """
        Get all token patterns registered for this dialect.

        Lazy-loads patterns on first access to avoid circular import issues.

        Returns:
            List of TokenPattern objects
        """
        if not self._token_patterns_initialized:
            self._register_token_patterns()
            self._token_patterns_initialized = True
        return self._token_patterns.copy()

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this dialect (e.g., 'sqlserver', 'postgresql')."""
        pass

    @property
    @abstractmethod
    def keywords(self) -> Set[str]:
        """Set of SQL keywords for this dialect (lowercase)."""
        pass

    @property
    def data_types(self) -> Set[str]:
        """Set of data type names (subset of keywords, used for categorization)."""
        return set()

    @property
    def functions(self) -> Set[str]:
        """Set of built-in function names (subset of keywords)."""
        return set()

    @property
    def ddl_object_keywords(self) -> Set[str]:
        """Set of DDL keywords that precede object names (e.g., TABLE, INDEX, VIEW)."""
        return {
            "table",
            "index",
            "view",
            "procedure",
            "function",
            "trigger",
            "type",
            "schema",
            "database",
        }

    @property
    def identifier_chars(self) -> str:
        """
        Special characters allowed in identifiers.

        Examples:
        - SQL Server: '@#$' (for @variables, #temp tables)
        - PostgreSQL: '$' (for $1, $var)
        - MySQL: '' (no special chars)
        """
        return ""

    @property
    def quote_chars(self) -> Dict[str, str]:
        """
        Quote characters for identifiers and strings.

        Returns:
            Dictionary with 'identifier' and 'string' keys.

        Examples:
        - SQL Server: {'identifier': '[', 'string': "'"}
        - PostgreSQL: {'identifier': '"', 'string': "'"}
        - MySQL: {'identifier': '`', 'string': "'"}
        """
        return {"identifier": '"', "string": "'"}

    @property
    def comment_styles(self) -> List[str]:
        """
        List of comment patterns supported by this dialect.

        Returns:
            List of comment prefixes (e.g., ['--', '#', '/*'])
        """
        return ["--", "/*"]

    def is_keyword(self, token: str) -> bool:
        """
        Check if a token is a keyword in this dialect.

        Args:
            token: The token to check (case-insensitive)

        Returns:
            True if the token is a keyword, False otherwise
        """
        return token.lower() in self.keywords

    def is_data_type(self, token: str) -> bool:
        """
        Check if a token is a data type in this dialect.

        Args:
            token: The token to check (case-insensitive)

        Returns:
            True if the token is a data type, False otherwise
        """
        return token.lower() in self.data_types

    def is_function(self, token: str) -> bool:
        """
        Check if a token is a built-in function in this dialect.

        Args:
            token: The token to check (case-insensitive)

        Returns:
            True if the token is a built-in function, False otherwise
        """
        return token.lower() in self.functions

    def is_ddl_object_keyword(self, token: str) -> bool:
        """
        Check if a token is a DDL object keyword (TABLE, INDEX, etc.).

        Args:
            token: The token to check (case-insensitive)

        Returns:
            True if the token is a DDL object keyword, False otherwise
        """
        return token.lower() in self.ddl_object_keywords

    def normalize_identifier(self, identifier: str) -> str:
        """
        Normalize an identifier for this dialect.

        Args:
            identifier: The identifier to normalize

        Returns:
            Normalized identifier (e.g., stripped quotes, case-adjusted)
        """
        # Default implementation: strip quotes and return as-is
        id_quote = self.quote_chars.get("identifier", '"')

        # Handle different quote styles
        if id_quote == "[" and identifier.startswith("[") and identifier.endswith("]"):
            return identifier[1:-1]
        elif identifier.startswith(id_quote) and identifier.endswith(id_quote):
            return identifier[1:-1]

        return identifier

    def _validate(self):
        """Validate that the dialect is properly configured."""
        if not self.name:
            raise ValueError(f"{self.__class__.__name__} must define a 'name' property")
        if not self.keywords:
            raise ValueError(
                f"{self.__class__.__name__} must define a 'keywords' property"
            )

    def __repr__(self) -> str:
        """String representation of the dialect."""
        return f"{self.__class__.__name__}(name='{self.name}', keywords={len(self.keywords)})"
