class APKMirrorScrapperFailure(Exception):
    """Failed to scrap icon from apkmirror."""

    pass


class PatchingFailed(Exception):
    """Patching Failed."""

    pass


class AppNotFound(ValueError):
    """Not a valid Revanced App."""

    pass


class PatchesJsonFailed(ValueError):
    """Patches failed."""

    pass
