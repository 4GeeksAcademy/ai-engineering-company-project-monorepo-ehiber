class AnalysisInputError(ValueError):
    """Raised when an incidents input file cannot be analyzed."""


class ExportUnavailableError(FileNotFoundError):
    """Raised when an analysis export does not exist yet."""
