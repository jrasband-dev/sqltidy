"""
SQL-specific pattern matchers.

These patterns match common SQL constructs like JOINs, clauses, subqueries, etc.
"""

from typing import List, Union, Optional, Set
from .base import Pattern, Match
from .matchers import (
    KeywordMatcher, IdentifierMatcher, TokenMatcher, SequenceMatcher, 
    OptionalMatcher, AnyOfMatcher, BetweenMatcher, WhitespaceMatcher
)
from ..tokenizer import Token, TokenGroup, TokenType, GroupType


class JoinPattern(Pattern):
    """
    Match JOIN clauses with optional ON conditions.
    
    Matches patterns like:
        - INNER JOIN table
        - LEFT JOIN table ON condition
        - LEFT OUTER JOIN table AS alias ON condition
    
    Examples:
        JoinPattern()  # Match any JOIN
        JoinPattern(join_type="LEFT")  # Match only LEFT JOINs
        JoinPattern(require_on=True)  # Match only JOINs with ON clause
    """
    
    JOIN_TYPES = {
        'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS',
        'LEFT OUTER', 'RIGHT OUTER', 'FULL OUTER'
    }
    
    def __init__(self, join_type: Optional[str] = None, require_on: bool = False):
        """
        Initialize JOIN pattern matcher.
        
        Args:
            join_type: Specific JOIN type to match (None = any type)
            require_on: Whether to require an ON clause
        """
        self.join_type = join_type.upper() if join_type else None
        self.require_on = require_on
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        matched_tokens = []
        current_pos = start
        metadata = {}
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    current_pos += 1
                    continue
            break
        
        if current_pos >= len(tokens):
            return None
        
        # Try to match JOIN keywords (INNER JOIN, LEFT JOIN, etc.)
        join_keyword_parts = []
        temp_pos = current_pos
        
        # Check for modifier keywords (INNER, LEFT, RIGHT, FULL)
        if temp_pos < len(tokens) and isinstance(tokens[temp_pos], Token):
            token = tokens[temp_pos]
            if token.type == TokenType.KEYWORD and token.value.upper() in ('INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS'):
                join_keyword_parts.append(token.value.upper())
                temp_pos += 1
                
                # Skip whitespace
                while temp_pos < len(tokens) and isinstance(tokens[temp_pos], Token):
                    if tokens[temp_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        temp_pos += 1
                    else:
                        break
                
                # Check for OUTER
                if temp_pos < len(tokens) and isinstance(tokens[temp_pos], Token):
                    if tokens[temp_pos].type == TokenType.KEYWORD and tokens[temp_pos].value.upper() == 'OUTER':
                        join_keyword_parts.append('OUTER')
                        temp_pos += 1
                        
                        # Skip whitespace
                        while temp_pos < len(tokens) and isinstance(tokens[temp_pos], Token):
                            if tokens[temp_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                temp_pos += 1
                            else:
                                break
        
        # Must have JOIN keyword
        if temp_pos >= len(tokens):
            return None
        
        if isinstance(tokens[temp_pos], Token):
            token = tokens[temp_pos]
            if token.type == TokenType.KEYWORD and token.value.upper() == 'JOIN':
                join_keyword_parts.append('JOIN')
                temp_pos += 1
            else:
                return None
        else:
            return None
        
        # Check if join type matches filter
        detected_join_type = ' '.join(join_keyword_parts)
        metadata['join_type'] = detected_join_type
        
        if self.join_type:
            if self.join_type != detected_join_type:
                return None
        
        # Collect matched tokens up to this point
        matched_tokens = tokens[start:temp_pos]
        current_pos = temp_pos
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(tokens[current_pos])
                    current_pos += 1
                    continue
            break
        
        # Match table name
        if current_pos >= len(tokens):
            return None
        
        if isinstance(tokens[current_pos], Token):
            token = tokens[current_pos]
            if token.type == TokenType.IDENTIFIER:
                metadata['table'] = token.value
                matched_tokens.append(token)
                current_pos += 1
            else:
                return None
        else:
            return None
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(tokens[current_pos])
                    current_pos += 1
                    continue
            break
        
        # Check for optional alias (with or without AS)
        if current_pos < len(tokens) and isinstance(tokens[current_pos], Token):
            token = tokens[current_pos]
            
            # Check for AS keyword
            if token.type == TokenType.KEYWORD and token.value.upper() == 'AS':
                matched_tokens.append(token)
                current_pos += 1
                
                # Skip whitespace
                while current_pos < len(tokens):
                    if isinstance(tokens[current_pos], Token):
                        if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            matched_tokens.append(tokens[current_pos])
                            current_pos += 1
                            continue
                    break
                
                # Get alias
                if current_pos < len(tokens) and isinstance(tokens[current_pos], Token):
                    if tokens[current_pos].type == TokenType.IDENTIFIER:
                        metadata['alias'] = tokens[current_pos].value
                        matched_tokens.append(tokens[current_pos])
                        current_pos += 1
            
            # Check for alias without AS
            elif token.type == TokenType.IDENTIFIER:
                # Peek ahead - if next non-whitespace is ON or another keyword, this is likely an alias
                peek_pos = current_pos + 1
                while peek_pos < len(tokens):
                    if isinstance(tokens[peek_pos], Token):
                        if tokens[peek_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                            peek_pos += 1
                            continue
                        elif tokens[peek_pos].type == TokenType.KEYWORD and tokens[peek_pos].value.upper() == 'ON':
                            # This is an alias
                            metadata['alias'] = token.value
                            matched_tokens.append(token)
                            current_pos += 1
                            break
                    break
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(tokens[current_pos])
                    current_pos += 1
                    continue
            break
        
        # Check for ON clause
        has_on = False
        if current_pos < len(tokens) and isinstance(tokens[current_pos], Token):
            if tokens[current_pos].type == TokenType.KEYWORD and tokens[current_pos].value.upper() == 'ON':
                has_on = True
                matched_tokens.append(tokens[current_pos])
                metadata['has_on'] = True
                current_pos += 1
        
        # Check requirement
        if self.require_on and not has_on:
            return None
        
        return Match(
            tokens=matched_tokens,
            start_index=start,
            end_index=current_pos,
            metadata=metadata
        )


class SelectClausePattern(Pattern):
    """
    Match SELECT clause up to FROM keyword.
    
    Examples:
        SelectClausePattern()  # Match entire SELECT clause
    """
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        # Must start with SELECT keyword
        if start >= len(tokens):
            return None
        
        # Skip whitespace
        current_pos = start
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    current_pos += 1
                    continue
            break
        
        if current_pos >= len(tokens):
            return None
        
        if not isinstance(tokens[current_pos], Token):
            return None
        
        if tokens[current_pos].type != TokenType.KEYWORD or tokens[current_pos].value.upper() != 'SELECT':
            return None
        
        # Collect tokens until we hit FROM, WHERE, or other clause keyword
        clause_ending_keywords = {'FROM', 'WHERE', 'GROUP', 'HAVING', 'ORDER', 'UNION', 'INTERSECT', 'EXCEPT'}
        matched_tokens = []
        
        for i in range(start, len(tokens)):
            token = tokens[i]
            
            # Check for clause-ending keyword (but not the initial SELECT)
            if i > start and isinstance(token, Token):
                if token.type == TokenType.KEYWORD and token.value.upper() in clause_ending_keywords:
                    return Match(
                        tokens=matched_tokens,
                        start_index=start,
                        end_index=i
                    )
            
            matched_tokens.append(token)
        
        # Reached end of tokens
        return Match(
            tokens=matched_tokens,
            start_index=start,
            end_index=len(tokens)
        )


class WhereClausePattern(Pattern):
    """
    Match WHERE clause.
    
    Examples:
        WhereClausePattern()  # Match entire WHERE clause
    """
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        # Must start with WHERE keyword
        if start >= len(tokens):
            return None
        
        # Skip whitespace
        current_pos = start
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    current_pos += 1
                    continue
            break
        
        if current_pos >= len(tokens):
            return None
        
        if not isinstance(tokens[current_pos], Token):
            return None
        
        if tokens[current_pos].type != TokenType.KEYWORD or tokens[current_pos].value.upper() != 'WHERE':
            return None
        
        # Collect tokens until we hit another clause keyword
        clause_ending_keywords = {'GROUP', 'HAVING', 'ORDER', 'UNION', 'INTERSECT', 'EXCEPT'}
        matched_tokens = []
        
        for i in range(start, len(tokens)):
            token = tokens[i]
            
            # Check for clause-ending keyword (but not the initial WHERE)
            if i > start and isinstance(token, Token):
                if token.type == TokenType.KEYWORD and token.value.upper() in clause_ending_keywords:
                    return Match(
                        tokens=matched_tokens,
                        start_index=start,
                        end_index=i
                    )
            
            matched_tokens.append(token)
        
        # Reached end of tokens
        return Match(
            tokens=matched_tokens,
            start_index=start,
            end_index=len(tokens)
        )


class SubqueryPattern(Pattern):
    """
    Match subqueries (SELECT within parentheses).
    
    Examples:
        SubqueryPattern()  # Match any (SELECT ...)
    """
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        if start >= len(tokens):
            return None
        
        item = tokens[start]
        
        # Check if it's a parenthesis group
        if isinstance(item, TokenGroup) and item.group_type == GroupType.PARENTHESIS:
            # Check if it contains SELECT
            inner_keywords = item.get_keywords()
            if 'SELECT' in inner_keywords:
                return Match(
                    tokens=[item],
                    start_index=start,
                    end_index=start + 1,
                    metadata={'is_subquery': True}
                )
        
        return None


class FunctionCallPattern(Pattern):
    """
    Match function calls.
    
    Examples:
        FunctionCallPattern()  # Match any function
        FunctionCallPattern(name="COUNT")  # Match COUNT() only
    """
    
    def __init__(self, name: Optional[str] = None):
        """
        Initialize function call pattern.
        
        Args:
            name: Specific function name to match (None = any function)
        """
        self.name = name.upper() if name else None
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        if start >= len(tokens):
            return None
        
        item = tokens[start]
        
        # Check if it's a function group
        if isinstance(item, TokenGroup) and item.group_type == GroupType.FUNCTION:
            if self.name:
                if item.name != self.name:
                    return None
            
            return Match(
                tokens=[item],
                start_index=start,
                end_index=start + 1,
                metadata={'function_name': item.name}
            )
        
        return None


class CaseExpressionPattern(Pattern):
    """
    Match CASE expressions.
    
    Examples:
        CaseExpressionPattern()  # Match CASE ... END
    """
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        # Must start with CASE keyword
        if start >= len(tokens):
            return None
        
        # Skip whitespace
        current_pos = start
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    current_pos += 1
                    continue
            break
        
        if current_pos >= len(tokens):
            return None
        
        if not isinstance(tokens[current_pos], Token):
            return None
        
        if tokens[current_pos].type != TokenType.KEYWORD or tokens[current_pos].value.upper() != 'CASE':
            return None
        
        # Find matching END keyword
        matched_tokens = []
        depth = 1  # Track nested CASE statements
        
        for i in range(start, len(tokens)):
            token = tokens[i]
            matched_tokens.append(token)
            
            if isinstance(token, Token) and token.type == TokenType.KEYWORD:
                if token.value.upper() == 'CASE':
                    if i > start:  # Don't count the initial CASE
                        depth += 1
                elif token.value.upper() == 'END':
                    depth -= 1
                    if depth == 0:
                        return Match(
                            tokens=matched_tokens,
                            start_index=start,
                            end_index=i + 1
                        )
        
        # Unmatched CASE
        return None


class CTEPattern(Pattern):
    """
    Match Common Table Expressions (WITH clause).
    
    Examples:
        CTEPattern()  # Match WITH ... AS (...)
    """
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        # Must start with WITH keyword
        if start >= len(tokens):
            return None
        
        # Skip whitespace
        current_pos = start
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    current_pos += 1
                    continue
            break
        
        if current_pos >= len(tokens):
            return None
        
        if not isinstance(tokens[current_pos], Token):
            return None
        
        if tokens[current_pos].type != TokenType.KEYWORD or tokens[current_pos].value.upper() != 'WITH':
            return None
        
        # Collect tokens until we hit SELECT/INSERT/UPDATE/DELETE
        main_query_keywords = {'SELECT', 'INSERT', 'UPDATE', 'DELETE'}
        matched_tokens = []
        paren_depth = 0
        
        for i in range(start, len(tokens)):
            token = tokens[i]
            matched_tokens.append(token)
            
            # Track parenthesis depth
            if isinstance(token, Token):
                if token.value == '(':
                    paren_depth += 1
                elif token.value == ')':
                    paren_depth -= 1
                
                # Check for main query start (outside parentheses)
                if paren_depth == 0 and i > start:
                    if token.type == TokenType.KEYWORD and token.value.upper() in main_query_keywords:
                        # Don't include the main query keyword
                        return Match(
                            tokens=matched_tokens[:-1],
                            start_index=start,
                            end_index=i
                        )
        
        # Reached end without finding main query
        return Match(
            tokens=matched_tokens,
            start_index=start,
            end_index=len(tokens)
        )


class GroupByPattern(Pattern):
    """
    Match GROUP BY clauses.
    
    Examples:
        GroupByPattern()  # Match GROUP BY ...
    """
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        current_pos = start
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    current_pos += 1
                    continue
            break
        
        if current_pos >= len(tokens):
            return None
        
        # Must start with GROUP keyword
        if not isinstance(tokens[current_pos], Token):
            return None
        if tokens[current_pos].type != TokenType.KEYWORD or tokens[current_pos].value.upper() != 'GROUP':
            return None
        
        matched_tokens = [tokens[current_pos]]
        current_pos += 1
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(tokens[current_pos])
                    current_pos += 1
                    continue
            break
        
        # Must have BY keyword
        if current_pos >= len(tokens):
            return None
        if not isinstance(tokens[current_pos], Token):
            return None
        if tokens[current_pos].type != TokenType.KEYWORD or tokens[current_pos].value.upper() != 'BY':
            return None
        
        matched_tokens.append(tokens[current_pos])
        current_pos += 1
        
        # Collect tokens until we hit a clause-ending keyword
        clause_ending_keywords = {'HAVING', 'ORDER', 'LIMIT', 'OFFSET', 'UNION', 'EXCEPT', 'INTERSECT', 'FETCH', 'FOR'}
        paren_depth = 0
        
        for i in range(current_pos, len(tokens)):
            token = tokens[i]
            
            if isinstance(token, Token):
                if token.value == '(':
                    paren_depth += 1
                elif token.value == ')':
                    paren_depth -= 1
                
                # Check for clause-ending keywords (outside parentheses)
                if paren_depth == 0 and token.type == TokenType.KEYWORD:
                    if token.value.upper() in clause_ending_keywords:
                        return Match(
                            tokens=matched_tokens,
                            start_index=start,
                            end_index=i,
                            metadata={'column_count': matched_tokens.count(Token(',', TokenType.PUNCTUATION)) + 1}
                        )
            
            matched_tokens.append(token)
        
        # Reached end
        return Match(
            tokens=matched_tokens,
            start_index=start,
            end_index=len(tokens),
            metadata={'column_count': matched_tokens.count(Token(',', TokenType.PUNCTUATION)) + 1}
        )


class OrderByPattern(Pattern):
    """
    Match ORDER BY clauses.
    
    Examples:
        OrderByPattern()  # Match ORDER BY ...
    """
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        current_pos = start
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    current_pos += 1
                    continue
            break
        
        if current_pos >= len(tokens):
            return None
        
        # Must start with ORDER keyword
        if not isinstance(tokens[current_pos], Token):
            return None
        if tokens[current_pos].type != TokenType.KEYWORD or tokens[current_pos].value.upper() != 'ORDER':
            return None
        
        matched_tokens = [tokens[current_pos]]
        current_pos += 1
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(tokens[current_pos])
                    current_pos += 1
                    continue
            break
        
        # Must have BY keyword
        if current_pos >= len(tokens):
            return None
        if not isinstance(tokens[current_pos], Token):
            return None
        if tokens[current_pos].type != TokenType.KEYWORD or tokens[current_pos].value.upper() != 'BY':
            return None
        
        matched_tokens.append(tokens[current_pos])
        current_pos += 1
        
        # Collect tokens and track ASC/DESC
        clause_ending_keywords = {'LIMIT', 'OFFSET', 'UNION', 'EXCEPT', 'INTERSECT', 'FETCH', 'FOR'}
        paren_depth = 0
        has_asc = False
        has_desc = False
        
        for i in range(current_pos, len(tokens)):
            token = tokens[i]
            
            if isinstance(token, Token):
                if token.value == '(':
                    paren_depth += 1
                elif token.value == ')':
                    paren_depth -= 1
                
                # Track ASC/DESC
                if token.type == TokenType.KEYWORD:
                    if token.value.upper() == 'ASC':
                        has_asc = True
                    elif token.value.upper() == 'DESC':
                        has_desc = True
                    
                    # Check for clause-ending keywords (outside parentheses)
                    if paren_depth == 0 and token.value.upper() in clause_ending_keywords:
                        return Match(
                            tokens=matched_tokens,
                            start_index=start,
                            end_index=i,
                            metadata={
                                'column_count': matched_tokens.count(Token(',', TokenType.PUNCTUATION)) + 1,
                                'has_asc': has_asc,
                                'has_desc': has_desc
                            }
                        )
            
            matched_tokens.append(token)
        
        # Reached end
        return Match(
            tokens=matched_tokens,
            start_index=start,
            end_index=len(tokens),
            metadata={
                'column_count': matched_tokens.count(Token(',', TokenType.PUNCTUATION)) + 1,
                'has_asc': has_asc,
                'has_desc': has_desc
            }
        )


class HavingPattern(Pattern):
    """
    Match HAVING clauses.
    
    Examples:
        HavingPattern()  # Match HAVING ...
    """
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        current_pos = start
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    current_pos += 1
                    continue
            break
        
        if current_pos >= len(tokens):
            return None
        
        # Must start with HAVING keyword
        if not isinstance(tokens[current_pos], Token):
            return None
        if tokens[current_pos].type != TokenType.KEYWORD or tokens[current_pos].value.upper() != 'HAVING':
            return None
        
        matched_tokens = [tokens[current_pos]]
        current_pos += 1
        
        # Collect tokens until we hit a clause-ending keyword
        clause_ending_keywords = {'ORDER', 'LIMIT', 'OFFSET', 'UNION', 'EXCEPT', 'INTERSECT', 'FETCH', 'FOR'}
        paren_depth = 0
        
        for i in range(current_pos, len(tokens)):
            token = tokens[i]
            
            if isinstance(token, Token):
                if token.value == '(':
                    paren_depth += 1
                elif token.value == ')':
                    paren_depth -= 1
                
                # Check for clause-ending keywords (outside parentheses)
                if paren_depth == 0 and token.type == TokenType.KEYWORD:
                    if token.value.upper() in clause_ending_keywords:
                        return Match(
                            tokens=matched_tokens,
                            start_index=start,
                            end_index=i
                        )
            
            matched_tokens.append(token)
        
        # Reached end
        return Match(
            tokens=matched_tokens,
            start_index=start,
            end_index=len(tokens)
        )


class UnionPattern(Pattern):
    """
    Match UNION/UNION ALL clauses.
    
    Examples:
        UnionPattern()  # Match UNION or UNION ALL
    """
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        current_pos = start
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    current_pos += 1
                    continue
            break
        
        if current_pos >= len(tokens):
            return None
        
        # Must start with UNION keyword
        if not isinstance(tokens[current_pos], Token):
            return None
        if tokens[current_pos].type != TokenType.KEYWORD or tokens[current_pos].value.upper() != 'UNION':
            return None
        
        matched_tokens = [tokens[current_pos]]
        is_all = False
        current_pos += 1
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    matched_tokens.append(tokens[current_pos])
                    current_pos += 1
                    continue
            break
        
        # Check for ALL keyword
        if current_pos < len(tokens) and isinstance(tokens[current_pos], Token):
            if tokens[current_pos].type == TokenType.KEYWORD and tokens[current_pos].value.upper() == 'ALL':
                is_all = True
                matched_tokens.append(tokens[current_pos])
                current_pos += 1
        
        return Match(
            tokens=matched_tokens,
            start_index=start,
            end_index=current_pos,
            metadata={'is_all': is_all}
        )


class DistinctPattern(Pattern):
    """
    Match DISTINCT keyword in SELECT statements.
    
    Examples:
        DistinctPattern()  # Match SELECT DISTINCT
    """
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        current_pos = start
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    current_pos += 1
                    continue
            break
        
        if current_pos >= len(tokens):
            return None
        
        # Must be DISTINCT keyword
        if not isinstance(tokens[current_pos], Token):
            return None
        if tokens[current_pos].type != TokenType.KEYWORD or tokens[current_pos].value.upper() != 'DISTINCT':
            return None
        
        return Match(
            tokens=[tokens[current_pos]],
            start_index=start,
            end_index=current_pos + 1
        )


class LimitPattern(Pattern):
    """
    Match LIMIT/TOP/FETCH FIRST clauses.
    
    Examples:
        LimitPattern()  # Match LIMIT n, TOP n, or FETCH FIRST n ROWS
    """
    
    def match(self, tokens: List[Union[Token, TokenGroup]], start: int = 0) -> Optional[Match]:
        current_pos = start
        
        # Skip whitespace
        while current_pos < len(tokens):
            if isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                    current_pos += 1
                    continue
            break
        
        if current_pos >= len(tokens):
            return None
        
        if not isinstance(tokens[current_pos], Token):
            return None
        
        matched_tokens = []
        limit_type = None
        limit_value = None
        
        # Check for LIMIT keyword
        if tokens[current_pos].type == TokenType.KEYWORD and tokens[current_pos].value.upper() == 'LIMIT':
            limit_type = 'LIMIT'
            matched_tokens.append(tokens[current_pos])
            current_pos += 1
            
            # Skip whitespace
            while current_pos < len(tokens):
                if isinstance(tokens[current_pos], Token):
                    if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        matched_tokens.append(tokens[current_pos])
                        current_pos += 1
                        continue
                break
            
            # Get limit value
            if current_pos < len(tokens) and isinstance(tokens[current_pos], Token):
                if tokens[current_pos].type == TokenType.NUMBER:
                    limit_value = tokens[current_pos].value
                    matched_tokens.append(tokens[current_pos])
                    current_pos += 1
        
        # Check for TOP keyword (SQL Server)
        elif tokens[current_pos].type == TokenType.KEYWORD and tokens[current_pos].value.upper() == 'TOP':
            limit_type = 'TOP'
            matched_tokens.append(tokens[current_pos])
            current_pos += 1
            
            # Skip whitespace
            while current_pos < len(tokens):
                if isinstance(tokens[current_pos], Token):
                    if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                        matched_tokens.append(tokens[current_pos])
                        current_pos += 1
                        continue
                break
            
            # Get limit value (might be in parentheses)
            if current_pos < len(tokens):
                if isinstance(tokens[current_pos], Token):
                    if tokens[current_pos].value == '(':
                        matched_tokens.append(tokens[current_pos])
                        current_pos += 1
                        
                        # Skip whitespace
                        while current_pos < len(tokens):
                            if isinstance(tokens[current_pos], Token):
                                if tokens[current_pos].type in (TokenType.WHITESPACE, TokenType.NEWLINE):
                                    matched_tokens.append(tokens[current_pos])
                                    current_pos += 1
                                    continue
                            break
                    
                    if current_pos < len(tokens) and isinstance(tokens[current_pos], Token):
                        if tokens[current_pos].type == TokenType.NUMBER:
                            limit_value = tokens[current_pos].value
                            matched_tokens.append(tokens[current_pos])
                            current_pos += 1
        
        # Check for FETCH FIRST (standard SQL)
        elif tokens[current_pos].type == TokenType.KEYWORD and tokens[current_pos].value.upper() == 'FETCH':
            limit_type = 'FETCH'
            matched_tokens.append(tokens[current_pos])
            current_pos += 1
            
            # Skip whitespace and collect FIRST/NEXT n ROWS ONLY
            while current_pos < len(tokens):
                if isinstance(tokens[current_pos], Token):
                    matched_tokens.append(tokens[current_pos])
                    if tokens[current_pos].type == TokenType.NUMBER:
                        limit_value = tokens[current_pos].value
                    if tokens[current_pos].type == TokenType.KEYWORD and tokens[current_pos].value.upper() == 'ONLY':
                        current_pos += 1
                        break
                    current_pos += 1
                else:
                    break
        else:
            return None
        
        if matched_tokens:
            return Match(
                tokens=matched_tokens,
                start_index=start,
                end_index=current_pos,
                metadata={'limit_type': limit_type, 'limit_value': limit_value}
            )
        
        return None
