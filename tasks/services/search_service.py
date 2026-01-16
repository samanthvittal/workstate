"""
Search query service for parsing and sanitizing search queries.

This service handles advanced search operators (AND, OR, NOT, phrases, regex)
and converts them into PostgreSQL tsquery format for full-text search.
"""
import re
from typing import Optional


class SearchQueryService:
    """
    Service for parsing and sanitizing search queries for PostgreSQL full-text search.

    Supports:
    - AND operator: '&' or 'AND' keyword
    - OR operator: '|' or 'OR' keyword
    - NOT operator: '!' prefix or 'NOT' keyword
    - Phrase search: "exact phrase"
    - Regex patterns: REGEX: prefix
    """

    # Maximum regex pattern length to prevent ReDoS attacks
    MAX_REGEX_LENGTH = 200

    # Characters that need escaping in tsquery
    TSQUERY_SPECIAL_CHARS = r'[&|!():<>]'

    @classmethod
    def parse_search_query(cls, query_string: str) -> Optional[str]:
        """
        Parse search query string and convert to PostgreSQL tsquery format.

        Args:
            query_string: Raw search query from user input

        Returns:
            Sanitized tsquery string, or None if query is empty

        Examples:
            "urgent tasks" -> "urgent & tasks"
            "bug OR feature" -> "bug | feature"
            "!completed" -> "!completed"
            '"exact match"' -> "'exact match'"
        """
        if not query_string or not query_string.strip():
            return None

        query = query_string.strip()

        # Handle phrase search (quoted strings)
        phrase_pattern = r'"([^"]+)"'
        phrases = re.findall(phrase_pattern, query)

        # Replace phrases with placeholders to protect them during processing
        phrase_placeholders = {}
        for i, phrase in enumerate(phrases):
            placeholder = f"__PHRASE_{i}__"
            phrase_placeholders[placeholder] = phrase
            query = query.replace(f'"{phrase}"', placeholder)

        # Handle REGEX: prefix
        if query.upper().startswith('REGEX:'):
            regex_pattern = query[6:].strip()
            if cls._validate_regex_pattern(regex_pattern):
                # Return regex pattern wrapped for PostgreSQL
                return f"'{regex_pattern}'"
            else:
                # Fall back to treating as normal search if regex is invalid
                query = regex_pattern

        # Replace operator keywords with symbols
        query = re.sub(r'\bAND\b', '&', query, flags=re.IGNORECASE)
        query = re.sub(r'\bOR\b', '|', query, flags=re.IGNORECASE)
        query = re.sub(r'\bNOT\b', '!', query, flags=re.IGNORECASE)

        # Sanitize individual terms (but preserve operators)
        tokens = []
        parts = re.split(r'(\s+|[&|!()])', query)

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check if this is an operator or placeholder
            if part in ('&', '|', '!', '(', ')'):
                tokens.append(part)
            elif part in phrase_placeholders:
                # Restore phrase with single quotes for tsquery
                phrase = phrase_placeholders[part]
                sanitized_phrase = cls._sanitize_term(phrase)
                tokens.append(f"'{sanitized_phrase}'")
            else:
                # Regular term - sanitize and add
                sanitized_term = cls._sanitize_term(part)
                if sanitized_term:
                    tokens.append(sanitized_term)

        if not tokens:
            return None

        # Join tokens with AND operator if no operators specified
        result = cls._join_tokens_with_default_and(tokens)

        return result if result else None

    @classmethod
    def _sanitize_term(cls, term: str) -> str:
        """
        Sanitize a search term to prevent tsquery injection.

        Args:
            term: Single search term

        Returns:
            Sanitized term safe for tsquery
        """
        if not term:
            return ''

        # Remove special characters that could break tsquery syntax
        # Keep alphanumeric, spaces, hyphens, and underscores
        sanitized = re.sub(r'[^\w\s\-]', '', term, flags=re.UNICODE)

        # Remove extra whitespace
        sanitized = ' '.join(sanitized.split())

        return sanitized.strip()

    @classmethod
    def _join_tokens_with_default_and(cls, tokens: list) -> str:
        """
        Join tokens with AND operator where no explicit operator exists.

        Args:
            tokens: List of search tokens (terms and operators)

        Returns:
            Joined query string
        """
        if not tokens:
            return ''

        result = []
        operators = {'&', '|', '!', '(', ')'}

        for i, token in enumerate(tokens):
            # Add the token
            result.append(token)

            # Check if we need to add an AND between this token and the next
            if i < len(tokens) - 1:
                current_token = token
                next_token = tokens[i + 1]

                # Don't add AND if current or next is an operator (with some exceptions)
                # Add AND between:
                # - term and term
                # - term and (
                # - ) and term
                # - ) and (
                # Don't add AND after operators like & | !
                should_add_and = False

                if current_token not in operators and next_token not in operators:
                    # term followed by term
                    should_add_and = True
                elif current_token == ')' and next_token not in operators:
                    # ) followed by term
                    should_add_and = True
                elif current_token not in operators and next_token == '(':
                    # term followed by (
                    should_add_and = True
                elif current_token == ')' and next_token == '(':
                    # ) followed by (
                    should_add_and = True

                if should_add_and:
                    result.append('&')

        return ' '.join(result)

    @classmethod
    def _validate_regex_pattern(cls, pattern: str) -> bool:
        """
        Validate regex pattern to prevent ReDoS attacks.

        Args:
            pattern: Regex pattern string

        Returns:
            True if pattern is safe, False otherwise
        """
        if not pattern or len(pattern) > cls.MAX_REGEX_LENGTH:
            return False

        # Check for potentially dangerous patterns
        # Be more specific to avoid false positives
        dangerous_patterns = [
            r'\([^)]*\*\)[*+]',  # Nested quantifiers like (a*)*
            r'\([^)]*\+\)[*+]',  # Nested quantifiers like (a+)+
            r'\(\?\<',           # Lookbehind
            r'\(\?\=',           # Lookahead (positive)
        ]

        for danger in dangerous_patterns:
            if re.search(danger, pattern):
                return False

        # Try to compile the pattern to check validity
        try:
            re.compile(pattern)
            return True
        except re.error:
            return False

    @classmethod
    def sanitize_input(cls, query_string: str) -> str:
        """
        Sanitize user input for safe database querying.

        This is a convenience method that combines validation and sanitization.

        Args:
            query_string: Raw user input

        Returns:
            Sanitized query string safe for database operations
        """
        if not query_string:
            return ''

        # Limit query length
        max_length = 500
        query = query_string[:max_length].strip()

        # Remove null bytes and other control characters
        query = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', query)

        return query
