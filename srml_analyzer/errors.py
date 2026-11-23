class AnalyzerError(Exception):
    """Base exception for expected analyzer failures."""


class FormatError(AnalyzerError):
    """Raised when an input does not match the expected binary container."""
