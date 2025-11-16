"""Error translation and solution finding."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class ParsedError:
    """Represents a parsed error message."""

    error_type: str
    message: str
    language: Optional[str]
    framework: Optional[str]
    file_path: Optional[str]
    line_number: Optional[int]
    key_terms: list[str]


class ErrorParser:
    """Parses error messages and stack traces to extract key information."""

    # Language detection patterns (order matters - most specific first)
    LANGUAGE_PATTERNS = {
        "rust": [
            r"error\[E\d{4}\]:",
            r"cannot borrow",
            r"--> .+\.rs:\d+:\d+",
        ],
        "typescript": [
            r"at .+\.tsx?:\d+:\d+",
            r"\.tsx?:",
            r"TS\d{4}:",
        ],
        "javascript": [
            r"at .+\.jsx?:\d+:\d+",
            r"\.jsx?:",
            r"node_modules",
            r"Cannot read property",
            r"is not defined",
        ],
        "python": [
            r"File \"(.+)\.py\"",
            r"Traceback \(most recent call last\)",
            r"(ImportError|AttributeError|ModuleNotFoundError)",
        ],
        "java": [
            r"at .+\.java:\d+",
            r"Exception in thread",
            r"(NullPointerException|IllegalArgumentException)",
        ],
        "go": [
            r"panic:",
            r"goroutine \d+",
            r".+\.go:\d+",
        ],
    }

    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        "react": [r"react", r"jsx", r"useState", r"useEffect"],
        "vue": [r"vue", r"@vue", r"composition-api"],
        "angular": [r"angular", r"@angular", r"ngOnInit"],
        "django": [r"django", r"django\."],
        "flask": [r"flask", r"werkzeug"],
        "fastapi": [r"fastapi", r"pydantic", r"starlette"],
        "express": [r"express", r"app\.get", r"app\.post"],
        "nextjs": [r"next", r"getServerSideProps", r"getStaticProps"],
    }

    # Common error patterns (checked in order - most specific first)
    ERROR_TYPE_PATTERNS = {
        "python": {
            "AttributeError": r"AttributeError: '(.+)' object has no attribute '(.+)'",
            "TypeError": r"TypeError: (.+)",
            "ImportError": r"(ImportError|ModuleNotFoundError): (.+)",
            "ValueError": r"ValueError: (.+)",
            "KeyError": r"KeyError: (.+)",
        },
        "javascript": {
            # Web-specific errors (check first - most specific)
            "CORS Error": r"CORS policy|Access-Control-Allow-Origin|No.*Access-Control",
            "Fetch Error": r"fetch.*failed|Failed to fetch|NetworkError",
            "Cannot read property": r"Cannot read propert(?:y|ies) ['\"](.+?)['\"] of",
            "undefined is not": r"undefined is not (a function|an object)",
            "null is not": r"null is not (a function|an object)",
            # Standard errors (check after specific ones)
            "TypeError": r"TypeError: (.+)",
            "ReferenceError": r"ReferenceError: (.+)",
            "SyntaxError": r"SyntaxError: (.+)",
            "RangeError": r"RangeError: (.+)",
        },
        "typescript": {
            "CORS Error": r"CORS policy|Access-Control-Allow-Origin",
            "Fetch Error": r"fetch.*failed|Failed to fetch",
            "Cannot read property": r"Cannot read propert(?:y|ies) ['\"](.+?)['\"] of",
            "TypeError": r"TypeError: (.+)",
            "ReferenceError": r"ReferenceError: (.+)",
            "SyntaxError": r"SyntaxError: (.+)",
        },
        "rust": {
            "borrow error": r"borrow of moved value",
            "cannot borrow": r"cannot borrow",
            "lifetime error": r"lifetime (.+) may not live long enough",
            "type mismatch": r"expected (.+), found (.+)",
            "E0382": r"error\[E0382\]",
            "E0502": r"error\[E0502\]",
            "E0308": r"error\[E0308\]",
        },
    }

    def parse(
        self,
        error_message: str,
        language: Optional[str] = None,
        framework: Optional[str] = None,
    ) -> ParsedError:
        """
        Parse an error message to extract key information.

        Args:
            error_message: The error text or stack trace
            language: Programming language (auto-detected if None)
            framework: Framework name (auto-detected if None)

        Returns:
            ParsedError with extracted information
        """
        # Detect language if not provided
        if not language:
            language = self._detect_language(error_message)

        # Detect framework if not provided
        if not framework:
            framework = self._detect_framework(error_message)

        # Extract error type
        error_type = self._extract_error_type(error_message, language)

        # Extract file path and line number
        file_path, line_number = self._extract_location(error_message)

        # Extract key terms
        key_terms = self._extract_key_terms(error_message, error_type)

        # Clean message
        message = self._clean_message(error_message)

        return ParsedError(
            error_type=error_type or "Unknown Error",
            message=message,
            language=language,
            framework=framework,
            file_path=file_path,
            line_number=line_number,
            key_terms=key_terms,
        )

    def _detect_language(self, text: str) -> Optional[str]:
        """Detect programming language from error message."""
        text_lower = text.lower()

        scores = {}
        for lang, patterns in self.LANGUAGE_PATTERNS.items():
            score = sum(
                1 for pattern in patterns if re.search(pattern, text, re.IGNORECASE)
            )
            if score > 0:
                scores[lang] = score

        if scores:
            return max(scores, key=scores.get)
        return None

    def _detect_framework(self, text: str) -> Optional[str]:
        """Detect framework from error message."""
        text_lower = text.lower()

        for framework, patterns in self.FRAMEWORK_PATTERNS.items():
            if any(re.search(pattern, text_lower) for pattern in patterns):
                return framework
        return None

    def _extract_error_type(self, text: str, language: Optional[str]) -> Optional[str]:
        """Extract the error type/name."""
        # Check for common web errors first (language-agnostic)
        web_error_patterns = {
            "CORS Error": r"CORS policy|Access-Control-Allow-Origin|No.*Access-Control",
            "Fetch Error": r"fetch.*failed|Failed to fetch|NetworkError",
            "Cannot read property": r"Cannot read propert(?:y|ies) ['\"](.+?)['\"] of",
        }

        for error_name, pattern in web_error_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return error_name

        # Language-specific extraction if language is detected
        if language and language in self.ERROR_TYPE_PATTERNS:
            for error_name, pattern in self.ERROR_TYPE_PATTERNS[language].items():
                if re.search(pattern, text, re.IGNORECASE):
                    return error_name

        # Generic error type extraction as fallback
        match = re.search(r"([\w]+Error|[\w]+Exception):", text)
        if match:
            return match.group(1)

        return None

    def _extract_location(self, text: str) -> tuple[Optional[str], Optional[int]]:
        """Extract file path and line number."""
        # Python format: File "path.py", line 123
        match = re.search(r'File "(.+?)", line (\d+)', text)
        if match:
            return match.group(1), int(match.group(2))

        # JavaScript/TypeScript format: at path.js:123:45
        match = re.search(r"at (.+?):(\d+):\d+", text)
        if match:
            return match.group(1), int(match.group(2))

        # Rust format: --> path.rs:123:45
        match = re.search(r"--> (.+?):(\d+):\d+", text)
        if match:
            return match.group(1), int(match.group(2))

        return None, None

    def _extract_key_terms(self, text: str, error_type: Optional[str]) -> list[str]:
        """Extract key terms for searching."""
        terms = set()  # Use set to avoid duplicates

        # Important web/tech terms to always capture
        important_terms = [
            "CORS",
            "cors",
            "fetch",
            "async",
            "await",
            "Promise",
            "undefined",
            "null",
            "map",
            "filter",
            "reduce",
            "Access-Control-Allow-Origin",
            "XMLHttpRequest",
            "module",
            "import",
            "export",
            "require",
        ]

        # Extract important terms first
        text_lower = text.lower()
        for term in important_terms:
            if term.lower() in text_lower:
                terms.add(term)
                if len(terms) >= 3:  # Limit important terms to 3
                    break

        # Extract quoted strings (often property names or specific values)
        quoted = re.findall(r"'([^']+)'|\"([^\"]+)\"", text)
        for match in quoted:
            term = match[0] or match[1]
            # Keep short important terms, ignore paths
            if term and "/" not in term and "\\" not in term:
                # Allow short terms for property names like "map", "id", etc.
                if len(term) <= 15:  # Reasonable property name length
                    if not error_type or term.lower() != error_type.lower():
                        terms.add(term)
                        if len(terms) >= 5:
                            break

        # Extract technical terms (CamelCase, snake_case)
        technical = re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b|\b\w+_\w+\b", text)
        # Don't exclude undefined/null - they're useful search terms
        for term in technical:
            if not error_type or term != error_type:
                terms.add(term)
                if len(terms) >= 5:
                    break

        return list(terms)[:5]  # Return max 5 unique key terms

    def _clean_message(self, text: str) -> str:
        """Clean and extract the core error message."""
        # Try to find the main error line
        lines = text.strip().split("\n")

        # Look for the error line (usually contains "Error:" or "Exception:")
        for line in reversed(lines):
            if re.search(r"(Error|Exception):", line):
                return line.strip()

        # If no error line found, return first non-empty line
        for line in lines:
            if line.strip():
                return line.strip()

        return text.strip()

    def build_search_query(self, parsed: ParsedError) -> str:
        """Build an optimized search query from parsed error."""
        parts = []

        # Add language
        if parsed.language:
            parts.append(parsed.language)

        # Add framework
        if parsed.framework:
            parts.append(parsed.framework)

        # Add error type
        if parsed.error_type and parsed.error_type != "Unknown Error":
            parts.append(parsed.error_type)

        # Add key terms (limit to avoid overly specific queries)
        parts.extend(parsed.key_terms[:2])

        # Build query - don't use site filter as SearXNG handles this better
        # with its category-based engine selection
        query = " ".join(parts)

        # Add "error" or "fix" to help guide results
        if query:  # Only add if we have content
            query += " error fix"

        return query
