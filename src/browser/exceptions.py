"""Browser impl exceptions."""


class PageLoadError(Exception):
    """Implies that the page load checker mechanism failed."""


class JSONExtractError(Exception):
    """Implies that the json extractor mechanism failed or no such json."""
